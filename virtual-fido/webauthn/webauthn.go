// ================================================================================
// WebAuthn Data Types
// ================================================================================
//
// File: webauthn/webauthn.go
// Project: Orange USB/IP Web Interface - Virtual FIDO Component
// Purpose: WebAuthn specification data structures for CTAP2 protocol
//
// WebAuthn Entities:
//
//      PublicKeyCredentialRPEntity
//      ├── ID: Relying party identifier (e.g., "example.com")
//      └── Name: Human-readable name (e.g., "Example Corp")
//
//      PublicKeyCrendentialUserEntity
//      ├── ID: Opaque user handle (up to 64 bytes)
//      ├── Name: User account name (e.g., "john@example.com")
//      └── DisplayName: Friendly name (e.g., "John Doe")
//
// Credential Types:
//
//      PublicKeyCredentialDescriptor
//      ├── Type: Always "public-key"
//      ├── ID: Credential identifier (random bytes)
//      └── Transports: Hint about how to reach authenticator
//
//      PublicKeyCredentialParams
//      ├── Type: "public-key"
//      └── Alg: COSE algorithm ID (e.g., -7 for ES256)
//
// CBOR Encoding:
//
//      All structures use CBOR tags for binary serialization.
//      This is required by the CTAP2 protocol specification.
//
// ================================================================================
package webauthn

import (
        "encoding/hex"
        "fmt"

        "github.com/bulwarkid/virtual-fido/cose"
)

type PublicKeyCredentialRPEntity struct {
        ID   string `cbor:"id" json:"id"`
        Name string `cbor:"name" json:"name"`
}

func (rp PublicKeyCredentialRPEntity) String() string {
        return fmt.Sprintf("RPEntity{ ID: %s, Name: %s }",
                rp.ID, rp.Name)
}

type PublicKeyCrendentialUserEntity struct {
        ID          []byte `cbor:"id" json:"id"`
        DisplayName string `cbor:"displayName" json:"display_name"`
        Name        string `cbor:"name" json:"name"`
}

func (user PublicKeyCrendentialUserEntity) String() string {
        return fmt.Sprintf("User{ ID: %s, DisplayName: %s, Name: %s }",
                hex.EncodeToString(user.ID),
                user.DisplayName,
                user.Name)
}

type PublicKeyCredentialDescriptor struct {
        Type       string   `cbor:"type"`
        ID         []byte   `cbor:"id"`
        Transports []string `cbor:"transports,omitempty"`
}

type PublicKeyCredentialParams struct {
        Type      string               `cbor:"type"`
        Algorithm cose.COSEAlgorithmID `cbor:"alg"`
}

type KeyHandle struct {
        PrivateKey    []byte `cbor:"1,keyasint"`
        ApplicationID []byte `cbor:"2,keyasint"`
}
