// ================================================================================
// USB Mass Storage Device Emulation
// ================================================================================
//
// File: usb/usb_mass_storage.go
// Project: Orange USB/IP Web Interface - Virtual Storage Component
// Purpose: Emulates a USB Mass Storage (flash drive) device via USB/IP
//
// USB Device Properties:
//
//      This file defines how the virtual flash drive appears to the USB host:
//      - Bus ID: Dynamic (e.g., 2-3, 2-4, etc.)
//      - Vendor ID: 0x0951 (Kingston-like)
//      - Product ID: 0x1666 (DataTraveler-like)
//      - Device Class: 0x00 (Defined at interface level)
//      - Interface Class: 0x08 (Mass Storage)
//      - Interface Subclass: 0x06 (SCSI transparent command set)
//      - Interface Protocol: 0x50 (Bulk-Only Transport)
//
// USB Descriptors:
//   - Device Descriptor: Flash drive information
//   - Configuration Descriptor: Power and interface configuration
//   - Interface Descriptor: Mass Storage interface
//   - Endpoint Descriptors: Bulk IN/OUT endpoints
//
// Data Flow:
//
//      USB Host (OS) → USB/IP → USBMassStorageDevice → SCSI → File System
//
// BBB Transport (Bulk-Only):
//   - Command: 31-byte CBW (Command Block Wrapper)
//   - Data: Variable length data transfer
//   - Status: 13-byte CSW (Command Status Wrapper)
//
// ================================================================================
package usb

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"github.com/bulwarkid/virtual-fido/usbip"
	"github.com/bulwarkid/virtual-fido/util"
)

var mscLogger = util.NewLogger("[MSC] ", util.LogLevelTrace)

const (
	MSC_CLASS           = 0x08
	MSC_SUBCLASS_SCSI   = 0x06
	MSC_PROTOCOL_BBB    = 0x50
	
	CBW_SIGNATURE       = 0x43425355
	CSW_SIGNATURE       = 0x53425355
	
	CBW_LENGTH          = 31
	CSW_LENGTH          = 13
	
	CSW_STATUS_PASSED   = 0x00
	CSW_STATUS_FAILED   = 0x01
	CSW_STATUS_PHASE    = 0x02
	
	SCSI_INQUIRY                = 0x12
	SCSI_READ_CAPACITY_10       = 0x25
	SCSI_READ_10                = 0x28
	SCSI_WRITE_10               = 0x2A
	SCSI_TEST_UNIT_READY        = 0x00
	SCSI_REQUEST_SENSE          = 0x03
	SCSI_MODE_SENSE_6           = 0x1A
	SCSI_PREVENT_ALLOW_MEDIUM   = 0x1E
	SCSI_READ_FORMAT_CAPACITIES = 0x23
	
	BLOCK_SIZE          = 512
	DEFAULT_BLOCKS      = 2048
)

type CommandBlockWrapper struct {
	Signature         uint32
	Tag               uint32
	DataTransferLen   uint32
	Flags             uint8
	LUN               uint8
	CBLength          uint8
	CommandBlock      [16]byte
}

type CommandStatusWrapper struct {
	Signature   uint32
	Tag         uint32
	DataResidue uint32
	Status      uint8
}

type USBMassStorageDevice struct {
	busID         string
	devnum        uint32
	storagePath   string
	diskImage     []byte
	diskSize      int64
	blockCount    uint32
	requestBuffer *util.RequestBuffer
	mutex         sync.Mutex
	vendorID      uint16
	productID     uint16
	deviceName    string
	isPublished   bool
}

func NewUSBMassStorageDevice(busID string, devnum uint32, storagePath string, sizeMB int) *USBMassStorageDevice {
	blockCount := uint32((sizeMB * 1024 * 1024) / BLOCK_SIZE)
	if blockCount < DEFAULT_BLOCKS {
		blockCount = DEFAULT_BLOCKS
	}
	
	device := &USBMassStorageDevice{
		busID:         busID,
		devnum:        devnum,
		storagePath:   storagePath,
		diskSize:      int64(blockCount) * BLOCK_SIZE,
		blockCount:    blockCount,
		requestBuffer: util.MakeRequestBuffer(),
		vendorID:      0x0951,
		productID:     0x1666,
		deviceName:    "Virtual Flash",
		isPublished:   false,
	}
	
	device.initDiskImage()
	return device
}

func (device *USBMassStorageDevice) initDiskImage() {
	device.diskImage = make([]byte, device.diskSize)
	
	device.createFAT16BootSector()
	
	if device.storagePath != "" {
		device.syncFromFolder()
	}
	
	mscLogger.Printf("Initialized disk image: %d bytes, %d blocks\n", device.diskSize, device.blockCount)
}

func (device *USBMassStorageDevice) createFAT16BootSector() {
	boot := device.diskImage[0:512]
	
	boot[0] = 0xEB
	boot[1] = 0x3C
	boot[2] = 0x90
	
	copy(boot[3:11], []byte("MSDOS5.0"))
	
	binary.LittleEndian.PutUint16(boot[11:13], BLOCK_SIZE)
	boot[13] = 4
	binary.LittleEndian.PutUint16(boot[14:16], 1)
	boot[16] = 2
	binary.LittleEndian.PutUint16(boot[17:19], 512)
	binary.LittleEndian.PutUint16(boot[19:21], uint16(device.blockCount))
	boot[21] = 0xF8
	binary.LittleEndian.PutUint16(boot[22:24], 32)
	binary.LittleEndian.PutUint16(boot[24:26], 32)
	binary.LittleEndian.PutUint16(boot[26:28], 1)
	binary.LittleEndian.PutUint32(boot[28:32], 0)
	
	boot[36] = 0x80
	boot[38] = 0x29
	binary.LittleEndian.PutUint32(boot[39:43], 0x12345678)
	copy(boot[43:54], []byte("VIRTUALUSB "))
	copy(boot[54:62], []byte("FAT16   "))
	
	boot[510] = 0x55
	boot[511] = 0xAA
}

func (device *USBMassStorageDevice) syncFromFolder() {
	if device.storagePath == "" {
		return
	}
	
	files, err := os.ReadDir(device.storagePath)
	if err != nil {
		mscLogger.Printf("Error reading storage folder: %v\n", err)
		return
	}
	
	for _, file := range files {
		if !file.IsDir() {
			filePath := filepath.Join(device.storagePath, file.Name())
			data, err := os.ReadFile(filePath)
			if err != nil {
				mscLogger.Printf("Error reading file %s: %v\n", file.Name(), err)
				continue
			}
			mscLogger.Printf("Loaded file: %s (%d bytes)\n", file.Name(), len(data))
			_ = data
		}
	}
}

func (device *USBMassStorageDevice) BusID() string {
	return device.busID
}

func (device *USBMassStorageDevice) SetPublished(published bool) {
	device.isPublished = published
}

func (device *USBMassStorageDevice) IsPublished() bool {
	return device.isPublished
}

func (device *USBMassStorageDevice) DeviceSummary() usbip.USBIPDeviceSummary {
	summary := usbip.USBIPDeviceSummary{
		Header: usbip.USBIPDeviceSummaryHeader{
			Busnum:              2,
			Devnum:              device.devnum,
			Speed:               2,
			IdVendor:            device.vendorID,
			IdProduct:           device.productID,
			BcdDevice:           0x0100,
			BDeviceClass:        0,
			BDeviceSubclass:     0,
			BDeviceProtocol:     0,
			BConfigurationValue: 1,
			BNumConfigurations:  1,
			BNumInterfaces:      1,
		},
		DeviceInterface: usbip.USBIPDeviceInterface{
			BInterfaceClass:    MSC_CLASS,
			BInterfaceSubclass: MSC_SUBCLASS_SCSI,
			Padding:            MSC_PROTOCOL_BBB,
		},
	}
	
	path := fmt.Sprintf("/sys/devices/pci0000:00/0000:00:01.2/usb2/%s", device.busID)
	copy(summary.Header.Path[:], []byte(path))
	copy(summary.Header.BusID[:], []byte(device.busID))
	
	return summary
}

func (device *USBMassStorageDevice) RemoveWaitingRequest(id uint32) bool {
	return device.requestBuffer.CancelRequest(id)
}

func (device *USBMassStorageDevice) HandleMessage(id uint32, onFinish func(response []byte), endpoint uint32, setupBytes []byte, transferBuffer []byte) {
	mscLogger.Printf("MSC MESSAGE - Endpoint: %d, SetupLen: %d, DataLen: %d\n", endpoint, len(setupBytes), len(transferBuffer))
	
	switch endpoint {
	case 0:
		reply := device.handleControlMessage(setupBytes)
		onFinish(reply)
	case 1:
		device.handleBulkIn(id, onFinish, transferBuffer)
	case 2:
		device.handleBulkOut(id, onFinish, transferBuffer)
	default:
		mscLogger.Printf("Unknown endpoint: %d\n", endpoint)
		onFinish(nil)
	}
}

func (device *USBMassStorageDevice) handleControlMessage(setupBytes []byte) []byte {
	if len(setupBytes) < 8 {
		return nil
	}
	
	setup := util.ReadLE[usbSetupPacket](bytes.NewBuffer(setupBytes))
	mscLogger.Printf("Control message: %s\n", setup)
	
	switch setup.BRequest {
	case usbRequestGetDescriptor:
		descriptorType, index := getDescriptorTypeAndIndex(setup.WValue)
		return device.getDescriptor(descriptorType, index)
	case usbRequestSetConfiguration:
		return nil
	case usbRequestGetStatus:
		return []byte{0, 0}
	case 0xFE:
		return []byte{0}
	case 0xFF:
		return nil
	}
	
	return nil
}

func (device *USBMassStorageDevice) getDescriptor(descriptorType usbDescriptorType, index uint8) []byte {
	mscLogger.Printf("Get descriptor: type=%d, index=%d\n", descriptorType, index)
	
	switch descriptorType {
	case usbDescriptorDevice:
		return device.getDeviceDescriptor()
	case usbDescriptorConfiguration:
		return device.getConfigurationDescriptor()
	case usbDescriptorString:
		return device.getStringDescriptor(index)
	}
	
	return nil
}

func (device *USBMassStorageDevice) getDeviceDescriptor() []byte {
	desc := make([]byte, 18)
	desc[0] = 18
	desc[1] = 1
	binary.LittleEndian.PutUint16(desc[2:4], 0x0200)
	desc[4] = 0
	desc[5] = 0
	desc[6] = 0
	desc[7] = 64
	binary.LittleEndian.PutUint16(desc[8:10], device.vendorID)
	binary.LittleEndian.PutUint16(desc[10:12], device.productID)
	binary.LittleEndian.PutUint16(desc[12:14], 0x0100)
	desc[14] = 1
	desc[15] = 2
	desc[16] = 3
	desc[17] = 1
	return desc
}

func (device *USBMassStorageDevice) getConfigurationDescriptor() []byte {
	totalLen := 9 + 9 + 7 + 7
	desc := make([]byte, totalLen)
	
	desc[0] = 9
	desc[1] = 2
	binary.LittleEndian.PutUint16(desc[2:4], uint16(totalLen))
	desc[4] = 1
	desc[5] = 1
	desc[6] = 0
	desc[7] = 0x80
	desc[8] = 250
	
	iface := desc[9:18]
	iface[0] = 9
	iface[1] = 4
	iface[2] = 0
	iface[3] = 0
	iface[4] = 2
	iface[5] = MSC_CLASS
	iface[6] = MSC_SUBCLASS_SCSI
	iface[7] = MSC_PROTOCOL_BBB
	iface[8] = 0
	
	epIn := desc[18:25]
	epIn[0] = 7
	epIn[1] = 5
	epIn[2] = 0x81
	epIn[3] = 0x02
	binary.LittleEndian.PutUint16(epIn[4:6], 512)
	epIn[6] = 0
	
	epOut := desc[25:32]
	epOut[0] = 7
	epOut[1] = 5
	epOut[2] = 0x02
	epOut[3] = 0x02
	binary.LittleEndian.PutUint16(epOut[4:6], 512)
	epOut[6] = 0
	
	return desc
}

func (device *USBMassStorageDevice) getStringDescriptor(index uint8) []byte {
	var str string
	
	switch index {
	case 0:
		desc := []byte{4, 3, 0x09, 0x04}
		return desc
	case 1:
		str = "Orange USB/IP"
	case 2:
		str = device.deviceName
	case 3:
		str = "12345678"
	default:
		str = ""
	}
	
	if str == "" {
		return []byte{2, 3}
	}
	
	utf16 := make([]byte, 2+len(str)*2)
	utf16[0] = byte(len(utf16))
	utf16[1] = 3
	for i, c := range str {
		utf16[2+i*2] = byte(c)
		utf16[2+i*2+1] = 0
	}
	return utf16
}

var pendingData []byte
var pendingCSW []byte

func (device *USBMassStorageDevice) handleBulkOut(id uint32, onFinish func(response []byte), data []byte) {
	device.mutex.Lock()
	defer device.mutex.Unlock()
	
	if len(data) >= CBW_LENGTH {
		cbw := device.parseCBW(data)
		if cbw != nil && cbw.Signature == CBW_SIGNATURE {
			mscLogger.Printf("Received CBW: Tag=%d, Len=%d, Cmd=0x%02X\n", 
				cbw.Tag, cbw.DataTransferLen, cbw.CommandBlock[0])
			
			responseData, status := device.handleSCSICommand(cbw)
			
			pendingData = responseData
			pendingCSW = device.buildCSW(cbw.Tag, cbw.DataTransferLen-uint32(len(responseData)), status)
			
			mscLogger.Printf("Prepared response: %d bytes data, status=%d\n", len(responseData), status)
		}
	}
	
	onFinish(nil)
}

func (device *USBMassStorageDevice) handleBulkIn(id uint32, onFinish func(response []byte), transferBuffer []byte) {
	device.mutex.Lock()
	defer device.mutex.Unlock()
	
	if len(pendingData) > 0 {
		response := pendingData
		pendingData = nil
		mscLogger.Printf("Sending data: %d bytes\n", len(response))
		onFinish(response)
		return
	}
	
	if len(pendingCSW) > 0 {
		response := pendingCSW
		pendingCSW = nil
		mscLogger.Printf("Sending CSW\n")
		onFinish(response)
		return
	}
	
	device.requestBuffer.Request(id, onFinish)
}

func (device *USBMassStorageDevice) parseCBW(data []byte) *CommandBlockWrapper {
	if len(data) < CBW_LENGTH {
		return nil
	}
	
	cbw := &CommandBlockWrapper{
		Signature:       binary.LittleEndian.Uint32(data[0:4]),
		Tag:             binary.LittleEndian.Uint32(data[4:8]),
		DataTransferLen: binary.LittleEndian.Uint32(data[8:12]),
		Flags:           data[12],
		LUN:             data[13] & 0x0F,
		CBLength:        data[14] & 0x1F,
	}
	copy(cbw.CommandBlock[:], data[15:31])
	
	return cbw
}

func (device *USBMassStorageDevice) buildCSW(tag uint32, residue uint32, status uint8) []byte {
	csw := make([]byte, CSW_LENGTH)
	binary.LittleEndian.PutUint32(csw[0:4], CSW_SIGNATURE)
	binary.LittleEndian.PutUint32(csw[4:8], tag)
	binary.LittleEndian.PutUint32(csw[8:12], residue)
	csw[12] = status
	return csw
}

func (device *USBMassStorageDevice) handleSCSICommand(cbw *CommandBlockWrapper) ([]byte, uint8) {
	cmd := cbw.CommandBlock[0]
	
	switch cmd {
	case SCSI_INQUIRY:
		return device.handleInquiry(cbw), CSW_STATUS_PASSED
		
	case SCSI_READ_CAPACITY_10:
		return device.handleReadCapacity(), CSW_STATUS_PASSED
		
	case SCSI_READ_10:
		return device.handleRead10(cbw), CSW_STATUS_PASSED
		
	case SCSI_WRITE_10:
		return nil, CSW_STATUS_PASSED
		
	case SCSI_TEST_UNIT_READY:
		return nil, CSW_STATUS_PASSED
		
	case SCSI_REQUEST_SENSE:
		return device.handleRequestSense(), CSW_STATUS_PASSED
		
	case SCSI_MODE_SENSE_6:
		return device.handleModeSense6(), CSW_STATUS_PASSED
		
	case SCSI_PREVENT_ALLOW_MEDIUM:
		return nil, CSW_STATUS_PASSED
		
	case SCSI_READ_FORMAT_CAPACITIES:
		return device.handleReadFormatCapacities(), CSW_STATUS_PASSED
		
	default:
		mscLogger.Printf("Unknown SCSI command: 0x%02X\n", cmd)
		return nil, CSW_STATUS_FAILED
	}
}

func (device *USBMassStorageDevice) handleInquiry(cbw *CommandBlockWrapper) []byte {
	allocLen := int(cbw.CommandBlock[4])
	if allocLen == 0 {
		allocLen = 36
	}
	
	data := make([]byte, allocLen)
	data[0] = 0x00
	data[1] = 0x80
	data[2] = 0x02
	data[3] = 0x02
	data[4] = 31
	data[5] = 0
	data[6] = 0
	data[7] = 0
	
	copy(data[8:16], []byte("ORANGE  "))
	copy(data[16:32], []byte("Virtual Flash   "))
	copy(data[32:36], []byte("1.00"))
	
	return data
}

func (device *USBMassStorageDevice) handleReadCapacity() []byte {
	data := make([]byte, 8)
	lastBlock := device.blockCount - 1
	binary.BigEndian.PutUint32(data[0:4], lastBlock)
	binary.BigEndian.PutUint32(data[4:8], BLOCK_SIZE)
	return data
}

func (device *USBMassStorageDevice) handleRead10(cbw *CommandBlockWrapper) []byte {
	lba := binary.BigEndian.Uint32(cbw.CommandBlock[2:6])
	blocks := binary.BigEndian.Uint16(cbw.CommandBlock[7:9])
	
	mscLogger.Printf("READ_10: LBA=%d, Blocks=%d\n", lba, blocks)
	
	offset := int64(lba) * BLOCK_SIZE
	length := int64(blocks) * BLOCK_SIZE
	
	if offset+length > device.diskSize {
		return make([]byte, length)
	}
	
	return device.diskImage[offset : offset+length]
}

func (device *USBMassStorageDevice) handleRequestSense() []byte {
	data := make([]byte, 18)
	data[0] = 0x70
	data[2] = 0x00
	data[7] = 10
	data[12] = 0x00
	data[13] = 0x00
	return data
}

func (device *USBMassStorageDevice) handleModeSense6() []byte {
	data := make([]byte, 4)
	data[0] = 3
	data[1] = 0
	data[2] = 0
	data[3] = 0
	return data
}

func (device *USBMassStorageDevice) handleReadFormatCapacities() []byte {
	data := make([]byte, 12)
	data[3] = 8
	
	binary.BigEndian.PutUint32(data[4:8], device.blockCount)
	data[8] = 0x02
	data[9] = 0
	binary.BigEndian.PutUint16(data[10:12], BLOCK_SIZE)
	
	return data
}
