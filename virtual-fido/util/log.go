// ================================================================================
// Logging Utilities
// ================================================================================
//
// File: util/log.go
// Project: Orange USB/IP Web Interface - Virtual FIDO Component
// Purpose: Configurable logging system with multiple verbosity levels
//
// Log Levels (from most to least verbose):
//   - LogLevelUnsafe (0): Sensitive data (keys, credentials) - NEVER in production
//   - LogLevelTrace (1): Protocol-level details (every packet)
//   - LogLevelDebug (2): Development debugging information
//   - LogLevelEnabled (3): Always-on operational logs
//
// Usage:
//
//      logger := util.NewLogger("[PREFIX] ", util.LogLevelDebug)
//      logger.Println("Message")        // Only prints if level >= current level
//      logger.Printf("Value: %d", val)  // Formatted output
//
// Global Configuration:
//   - SetLogLevel(): Set minimum log level globally
//   - SetLogOutput(): Redirect log output (default: stdout)
//
// Buffer System:
//
//      Logs are buffered until an output writer is configured.
//      This prevents lost messages during initialization.
//
// ================================================================================
package util

import (
        "bytes"
        "io"
        "log"
)

var logLog = NewLogger("[LOG] ", LogLevelEnabled)

type LogLevel byte

const (
        LogLevelUnsafe  LogLevel = 0
        LogLevelTrace   LogLevel = 1
        LogLevelDebug   LogLevel = 2
        LogLevelEnabled LogLevel = 3
)

// Not sure if there is a standard library way to do this,
// but I couldn't find any at the moment
type logBuffer struct {
        buffer *bytes.Buffer
        output io.Writer
}

func newLogBuffer() *logBuffer {
        return &logBuffer{
                buffer: new(bytes.Buffer),
                output: nil,
        }
}

func (logBuf *logBuffer) Write(p []byte) (n int, err error) {
        if logBuf.output == nil {
                return logBuf.buffer.Write(p)
        } else {
                return logBuf.output.Write(p)
        }
}

func (logBuf *logBuffer) setOutput(output io.Writer) {
        if logBuf.buffer.Len() > 0 {
                b, _ := io.ReadAll(logBuf.buffer)
                output.Write(b)
        }
        logBuf.output = output
}

var enabledLogOutput *logBuffer = newLogBuffer()
var debugLogOutput *logBuffer = newLogBuffer()
var traceLogOutput *logBuffer = newLogBuffer()
var unsafeLogOutput *logBuffer = newLogBuffer()

func SetLogOutput(out io.Writer) {
        enabledLogOutput.setOutput(out)
}

func SetLogLevel(level LogLevel) {
        if level <= LogLevelUnsafe {
                unsafeLogOutput.setOutput(traceLogOutput)
        }
        if level <= LogLevelTrace {
                traceLogOutput.setOutput(debugLogOutput)
        }
        if level <= LogLevelDebug {
                debugLogOutput.setOutput(enabledLogOutput)
        }
        logLog.Printf("Log Level Set: %d\n", level)
}

func NewLogger(prefix string, level LogLevel) *log.Logger {
        if level == LogLevelEnabled {
                return log.New(enabledLogOutput, prefix, 0)
        } else if level == LogLevelDebug {
                return log.New(debugLogOutput, prefix, 0)
        } else if level == LogLevelTrace {
                return log.New(traceLogOutput, prefix, 0)
        } else {
                return log.New(unsafeLogOutput, prefix, 0)
        }
}
