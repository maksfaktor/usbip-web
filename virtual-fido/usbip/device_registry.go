// ================================================================================
// USB/IP Device Registry
// ================================================================================
//
// File: usbip/device_registry.go
// Project: Orange USB/IP Web Interface - Virtual FIDO Component
// Purpose: Dynamic device registration and management for USB/IP server
//
// This module provides:
//   - Global device registry for runtime device management
//   - Thread-safe device add/remove operations
//   - Device lookup by BusID
//   - HTTP API handlers for remote device management
//
// ================================================================================
package usbip

import (
	"encoding/json"
	"net/http"
	"sync"

	"github.com/bulwarkid/virtual-fido/util"
)

var registryLogger = util.NewLogger("[REGISTRY] ", util.LogLevelTrace)

type DeviceInfo struct {
	BusID       string `json:"busid"`
	Path        string `json:"path"`
	VendorID    string `json:"vendor_id"`
	ProductID   string `json:"product_id"`
	DeviceClass string `json:"device_class"`
	Description string `json:"description"`
	IsVirtual   bool   `json:"is_virtual"`
}

type DeviceRegistry struct {
	devices map[string]USBIPDevice
	mutex   sync.RWMutex
	server  *USBIPServer
}

var globalRegistry *DeviceRegistry
var registryOnce sync.Once

func GetGlobalRegistry() *DeviceRegistry {
	registryOnce.Do(func() {
		globalRegistry = &DeviceRegistry{
			devices: make(map[string]USBIPDevice),
		}
	})
	return globalRegistry
}

func (r *DeviceRegistry) SetServer(server *USBIPServer) {
	r.mutex.Lock()
	defer r.mutex.Unlock()
	r.server = server
}

func (r *DeviceRegistry) RegisterDevice(device USBIPDevice) error {
	r.mutex.Lock()
	defer r.mutex.Unlock()
	
	busID := device.BusID()
	r.devices[busID] = device
	
	if r.server != nil {
		r.server.devices = append(r.server.devices, device)
	}
	
	registryLogger.Printf("Device registered: %s\n", busID)
	return nil
}

func (r *DeviceRegistry) UnregisterDevice(busID string) error {
	r.mutex.Lock()
	defer r.mutex.Unlock()
	
	delete(r.devices, busID)
	
	if r.server != nil {
		newDevices := make([]USBIPDevice, 0)
		for _, d := range r.server.devices {
			if d.BusID() != busID {
				newDevices = append(newDevices, d)
			}
		}
		r.server.devices = newDevices
	}
	
	registryLogger.Printf("Device unregistered: %s\n", busID)
	return nil
}

func (r *DeviceRegistry) GetDevice(busID string) USBIPDevice {
	r.mutex.RLock()
	defer r.mutex.RUnlock()
	return r.devices[busID]
}

func (r *DeviceRegistry) ListDevices() []DeviceInfo {
	r.mutex.RLock()
	defer r.mutex.RUnlock()
	
	result := make([]DeviceInfo, 0, len(r.devices))
	
	for _, device := range r.devices {
		summary := device.DeviceSummary()
		info := DeviceInfo{
			BusID:       device.BusID(),
			VendorID:    formatHex(summary.Header.IdVendor),
			ProductID:   formatHex(summary.Header.IdProduct),
			DeviceClass: formatHex16(summary.DeviceInterface.BInterfaceClass),
			IsVirtual:   true,
		}
		
		if summary.DeviceInterface.BInterfaceClass == 0x08 {
			info.Description = "Virtual USB Flash Drive"
		} else if summary.DeviceInterface.BInterfaceClass == 0x03 {
			info.Description = "Virtual FIDO2 Security Key"
		} else {
			info.Description = "Virtual USB Device"
		}
		
		result = append(result, info)
	}
	
	return result
}

func formatHex(val uint16) string {
	return string([]byte{
		hexChar(byte(val >> 12 & 0xF)),
		hexChar(byte(val >> 8 & 0xF)),
		hexChar(byte(val >> 4 & 0xF)),
		hexChar(byte(val & 0xF)),
	})
}

func formatHex16(val uint8) string {
	return string([]byte{
		hexChar(val >> 4 & 0xF),
		hexChar(val & 0xF),
	})
}

func hexChar(b byte) byte {
	if b < 10 {
		return '0' + b
	}
	return 'a' + b - 10
}

func (r *DeviceRegistry) HandleListDevices(w http.ResponseWriter, req *http.Request) {
	devices := r.ListDevices()
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"devices": devices,
	})
}

type RegisterDeviceRequest struct {
	BusID       string `json:"busid"`
	DeviceType  string `json:"device_type"`
	StoragePath string `json:"storage_path,omitempty"`
	SizeMB      int    `json:"size_mb,omitempty"`
	Name        string `json:"name,omitempty"`
}

func (r *DeviceRegistry) HandleRegisterDevice(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	var request RegisterDeviceRequest
	if err := json.NewDecoder(req.Body).Decode(&request); err != nil {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"success": false,
			"error":   "Invalid request body",
		})
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Device registration handled by Flask API",
		"busid":   request.BusID,
	})
}

func (r *DeviceRegistry) HandleUnregisterDevice(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	var request struct {
		BusID string `json:"busid"`
	}
	if err := json.NewDecoder(req.Body).Decode(&request); err != nil {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"success": false,
			"error":   "Invalid request body",
		})
		return
	}
	
	if err := r.UnregisterDevice(request.BusID); err != nil {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		})
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Device unregistered",
	})
}

func StartAPIServer(port int) {
	registry := GetGlobalRegistry()
	
	http.HandleFunc("/api/devices", registry.HandleListDevices)
	http.HandleFunc("/api/devices/register", registry.HandleRegisterDevice)
	http.HandleFunc("/api/devices/unregister", registry.HandleUnregisterDevice)
	
	addr := ":3242"
	registryLogger.Printf("Starting API server on %s\n", addr)
	go http.ListenAndServe(addr, nil)
}
