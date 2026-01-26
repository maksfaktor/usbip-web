// ================================================================================
// CTAP HID Data Structures and Constants
// ================================================================================
//
// File: ctap_hid/data.go
// Project: Orange USB/IP Web Interface - Virtual FIDO Component
// Purpose: CTAP HID protocol constants and packet structures
//
// CTAP HID Overview:
//
//      CTAP HID is the USB HID transport layer for FIDO2/U2F protocols.
//      It fragments messages into 64-byte HID reports and manages channels.
//
// Packet Size: 64 bytes (fixed for USB HID)
//
// Broadcast Channel: 0xFFFFFFFF
//   - Used only for CTAPHID_INIT to allocate new channels
//   - All other commands require allocated channel
//
// HID Commands (7th bit set):
//   - CTAPHID_MSG (0x83): U2F message
//   - CTAPHID_CBOR (0x90): CTAP2 CBOR command
//   - CTAPHID_INIT (0x86): Initialize/allocate channel
//   - CTAPHID_PING (0x81): Echo test
//   - CTAPHID_CANCEL (0x91): Cancel operation
//   - CTAPHID_ERROR (0xBF): Error response
//   - CTAPHID_KEEPALIVE (0xBB): Keep connection alive
//   - CTAPHID_WINK (0x88): Visual indicator
//   - CTAPHID_LOCK (0x84): Lock channel
//
// Keepalive Status:
//   - 2 (UPNEEDED): User presence required (touch button)
//
// ================================================================================
package ctap_hid

import (
        "fmt"
)

const (
        ctapHIDMaxPacketSize int = 64
)

const ctapHIDStatusUpneeded uint8 = 2

type ctapHIDChannelID uint32

const (
        ctapHIDBroadcastChannel ctapHIDChannelID = 0xFFFFFFFF
)

type ctapHIDCommand uint8

const (
        // Each CTAPHID command has its seventh bit set for easier reading
        ctapHIDCommandMsg       ctapHIDCommand = 0x83
        ctapHIDCommandCBOR      ctapHIDCommand = 0x90
        ctapHIDCommandInit      ctapHIDCommand = 0x86
        ctapHIDCommandPing      ctapHIDCommand = 0x81
        ctapHIDCommandCancel    ctapHIDCommand = 0x91
        ctapHIDCommandError     ctapHIDCommand = 0xBF
        ctapHIDCommandKeepalive ctapHIDCommand = 0xBB
        ctapHIDCommandWink      ctapHIDCommand = 0x88
        ctapHIDCommandLock      ctapHIDCommand = 0x84
)

var ctapHIDCommandDescriptions = map[ctapHIDCommand]string{
        ctapHIDCommandMsg:       "ctapHIDCommandMsg",
        ctapHIDCommandCBOR:      "ctapHIDCommandCBOR",
        ctapHIDCommandInit:      "ctapHIDCommandInit",
        ctapHIDCommandPing:      "ctapHIDCommandPing",
        ctapHIDCommandCancel:    "ctapHIDCommandCancel",
        ctapHIDCommandError:     "ctapHIDCommandError",
        ctapHIDCommandKeepalive: "ctapHIDCommandKeepalive",
        ctapHIDCommandWink:      "ctapHIDCommandWink",
        ctapHIDCommandLock:      "ctapHIDCommandLock",
}

type ctapHIDErrorCode uint8

const (
        ctapHIDErrorInvalidCommand   ctapHIDErrorCode = 0x01
        ctapHIDErrorInvalidParameter ctapHIDErrorCode = 0x02
        ctapHIDErrorInvalidLength    ctapHIDErrorCode = 0x03
        ctapHIDErrorInvalidSequence  ctapHIDErrorCode = 0x04
        ctapHIDErrorMessageTimeout   ctapHIDErrorCode = 0x05
        ctapHIDErrorChannelBusy      ctapHIDErrorCode = 0x06
        ctapHIDErrorLockRequired     ctapHIDErrorCode = 0x0A
        ctapHIDErrorInvalidChannel   ctapHIDErrorCode = 0x0B
        ctapHIDErrorOther            ctapHIDErrorCode = 0x7F
)

var ctapHIDErrorCodeDescriptions = map[ctapHIDErrorCode]string{
        ctapHIDErrorInvalidCommand:   "ctapHIDErrInvalidCommand",
        ctapHIDErrorInvalidParameter: "ctapHIDErrInvalidParameter",
        ctapHIDErrorInvalidLength:    "ctapHIDErrInvalidLength",
        ctapHIDErrorInvalidSequence:  "ctapHIDErrInvalidSequence",
        ctapHIDErrorMessageTimeout:   "ctapHIDErrMessageTimeout",
        ctapHIDErrorChannelBusy:      "ctapHIDErrChannelBusy",
        ctapHIDErrorLockRequired:     "ctapHIDErrLockRequired",
        ctapHIDErrorInvalidChannel:   "ctapHIDErrInvalidChannel",
        ctapHIDErrorOther:            "ctapHIDErrOther",
}

func ctapHidError(channelId ctapHIDChannelID, err ctapHIDErrorCode) [][]byte {
        ctapHIDLogger.Printf("CTAPHID ERROR: %s\n\n", ctapHIDErrorCodeDescriptions[err])
        return createResponsePackets(channelId, ctapHIDCommandError, []byte{byte(err)})
}

type ctapHIDCapabilityFlag uint8

const (
        ctapHIDCapabilityWink  ctapHIDCapabilityFlag = 0x1
        ctapHIDCapabilityCBOR  ctapHIDCapabilityFlag = 0x4
        ctapHIDCapabilityNoMsg ctapHIDCapabilityFlag = 0x8
)

type ctapHIDMessageHeader struct {
        ChannelID     ctapHIDChannelID
        Command       ctapHIDCommand
        PayloadLength uint16
}

func (header ctapHIDMessageHeader) String() string {
        description, ok := ctapHIDCommandDescriptions[header.Command]
        if !ok {
                description = fmt.Sprintf("0x%x", header.Command)
        }
        channelDesc := fmt.Sprintf("0x%x", header.ChannelID)
        if header.ChannelID == ctapHIDBroadcastChannel {
                channelDesc = "CTAPHID_BROADCAST_CHANNEL"
        }
        return fmt.Sprintf("CTAPHIDMessageHeader{ ChannelID: %s, Command: %s, PayloadLength: %d }",
                channelDesc,
                description,
                header.PayloadLength)
}
