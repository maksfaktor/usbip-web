// ================================================================================
// USB/IP Client - Linux/Windows Platform Implementation
// ================================================================================
//
// File: client_usbip.go
// Project: Orange USB/IP Web Interface - Virtual FIDO Component
// Build Tags: linux || windows
//
// Purpose:
//
//      Implements the virtual FIDO2 device using USB/IP protocol for Linux and
//      Windows platforms. This creates a TCP server that emulates a USB HID device
//      over the network, allowing the virtual security key to be attached via USB/IP.
//
// Protocol Stack (bottom to top):
//
//      1. USB/IP Server (port 3241) - Network transport layer
//      2. USB Device - Emulates USB HID FIDO device descriptors
//      3. CTAP HID Server - USB HID transport for CTAP/U2F
//      4. CTAP Server - CTAP2 (WebAuthn) command processing
//      5. U2F Server - Legacy U2F command processing
//      6. FIDO Client - Application logic (credential storage, user verification)
//
// Port Configuration:
//   - Virtual FIDO runs on port 3241 (separate from real usbipd on 3240)
//   - Accepts connections only from 127.0.0.1 for security
//
// Attachment Workflow:
//
//      1. Start virtual-fido binary → USB/IP server listens on :3241
//      2. modprobe vhci-hcd → Load kernel module for virtual USB host
//      3. usbip --tcp-port 3241 attach -r 127.0.0.1 -b 2-2 → Attach device
//      4. Device appears in lsusb as "0000:0000 Virtual FIDO"
//
// ================================================================================
//go:build linux || windows

package virtual_fido

import (
        "github.com/bulwarkid/virtual-fido/ctap"
        "github.com/bulwarkid/virtual-fido/ctap_hid"
        "github.com/bulwarkid/virtual-fido/u2f"
        "github.com/bulwarkid/virtual-fido/usb"
        "github.com/bulwarkid/virtual-fido/usbip"
)

func startClient(client FIDOClient) {
        ctapServer := ctap.NewCTAPServer(client)
        u2fServer := u2f.NewU2FServer(client)
        ctapHIDServer := ctap_hid.NewCTAPHIDServer(ctapServer, u2fServer)
        usbDevice := usb.NewUSBDevice(ctapHIDServer)
        server := usbip.NewUSBIPServer([]usbip.USBIPDevice{usbDevice})
        server.Start()
}
