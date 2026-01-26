// ================================================================================
// Virtual FIDO - Main Entry Point
// ================================================================================
//
// File: virtual_fido.go
// Project: Orange USB/IP Web Interface - Virtual FIDO Component
// Purpose: Main library entry point for starting the virtual FIDO2 security key
//
// Architecture:
//
//      This is the root package that provides the high-level API for the virtual
//      FIDO2 device. It abstracts platform-specific implementations (Mac vs USB/IP)
//      and provides a unified interface for client applications.
//
// Key Components:
//   - FIDOClient interface: Combined U2F and CTAP2 client capabilities
//   - Start(): Entry point to launch the virtual device (platform-aware)
//   - Logging configuration: Control verbosity and output destination
//
// Platform Support:
//   - Linux/Windows: Uses USB/IP protocol on port 3241
//   - macOS: Uses native HID driver (client_mac.go)
//
// Usage:
//
//      client := fido_client.NewDefaultClient()
//      virtual_fido.SetLogLevel(util.LogLevelDebug)
//      virtual_fido.Start(client)  // Blocks and serves FIDO requests
//
// ================================================================================
package virtual_fido

import (
        "io"

        "github.com/bulwarkid/virtual-fido/ctap"
        "github.com/bulwarkid/virtual-fido/u2f"
        "github.com/bulwarkid/virtual-fido/util"
)

type FIDOClient interface {
        u2f.U2FClient
        ctap.CTAPClient
}

func Start(client FIDOClient) {
        // Calls either the Mac or USB/IP client, based on system
        startClient(client)
}

func SetLogLevel(level util.LogLevel) {
        util.SetLogLevel(level)
}

func SetLogOutput(out io.Writer) {
        util.SetLogOutput(out)
}
