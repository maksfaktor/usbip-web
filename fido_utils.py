"""
FIDO2 Virtual Device Utilities
Python wrapper for virtual-fido CLI commands
"""

import subprocess
import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Configuration - Universal paths supporting any Linux user
# Automatically detect home directory and project directory
HOME = os.path.expanduser('~')  # Works on any system: /home/runner, /home/maxx, etc.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))  # Current project directory

# Environment variable names
PASSPHRASE_ENV_VAR = 'FIDO_PASSPHRASE'
VAULT_PATH_ENV_VAR = 'FIDO_VAULT_PATH'
BINARY_PATH_ENV_VAR = 'FIDO_BINARY_PATH'
DATA_DIR_ENV_VAR = 'FIDO_DATA_DIR'

# Default values with environment variable overrides
DEFAULT_PASSPHRASE = 'passphrase'

# FIDO binary path: check env var, then ~/fido_data, then project dir
def get_fido_binary_path():
    """Find FIDO binary in order: env var -> ~/fido_data -> project dir"""
    # Check environment variable first
    env_path = os.environ.get(BINARY_PATH_ENV_VAR)
    if env_path and os.path.isfile(env_path):
        return env_path
    
    # Check ~/fido_data/virtual-fido (installed by install script)
    user_binary = os.path.join(HOME, 'fido_data', 'virtual-fido')
    if os.path.isfile(user_binary):
        return user_binary
    
    # Fallback to project directory
    project_binary = os.path.join(PROJECT_DIR, 'virtual-fido', 'cmd', 'demo', 'virtual-fido-demo')
    if os.path.isfile(project_binary):
        return project_binary
    
    # Return default path (will show error when used)
    return user_binary

FIDO_BINARY = get_fido_binary_path()

# FIDO data directory: check env var, then fallback to ~/fido_data
FIDO_DATA_DIR = os.environ.get(
    DATA_DIR_ENV_VAR,
    os.path.join(HOME, 'fido_data')
)

# FIDO vault path: check env var, then fallback to FIDO_DATA_DIR/vault.json
FIDO_VAULT_PATH = os.environ.get(
    VAULT_PATH_ENV_VAR,
    os.path.join(FIDO_DATA_DIR, 'vault.json')
)


def get_fido_passphrase() -> str:
    """
    Get FIDO passphrase from environment variable or use default
    
    Returns:
        Current passphrase (from env or default)
    """
    return os.environ.get(PASSPHRASE_ENV_VAR, DEFAULT_PASSPHRASE)


def set_fido_passphrase(new_passphrase: str) -> Dict:
    """
    Set FIDO passphrase in environment variable
    
    NOTE: Environment variable changes are only valid for current process.
    For permanent storage, add to .env file or system environment.
    
    Args:
        new_passphrase: New passphrase to set
        
    Returns:
        Dict with success status and message
    """
    try:
        if not new_passphrase or len(new_passphrase) < 8:
            return {
                'success': False,
                'error': 'Passphrase must be at least 8 characters long'
            }
        
        # Set environment variable
        os.environ[PASSPHRASE_ENV_VAR] = new_passphrase
        logger.info("FIDO passphrase updated in environment")
        
        return {
            'success': True,
            'message': 'Passphrase updated successfully'
        }
    except Exception as e:
        logger.error(f"Error setting passphrase: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def get_vault_path() -> str:
    """
    Get current vault path from environment variable or use default
    
    Returns:
        Current vault path
    """
    return os.environ.get(VAULT_PATH_ENV_VAR, FIDO_VAULT_PATH)


def set_vault_path(new_path: str) -> Dict:
    """
    Set vault path in environment variable
    
    Args:
        new_path: New vault file path
        
    Returns:
        Dict with success status and message
    """
    try:
        if not new_path:
            return {
                'success': False,
                'error': 'Vault path cannot be empty'
            }
        
        # Ensure directory exists
        vault_dir = os.path.dirname(new_path)
        if not os.path.exists(vault_dir):
            os.makedirs(vault_dir, exist_ok=True)
            logger.info(f"Created vault directory: {vault_dir}")
        
        # Set environment variable
        os.environ[VAULT_PATH_ENV_VAR] = new_path
        logger.info(f"Vault path updated to: {new_path}")
        
        return {
            'success': True,
            'message': f'Vault path updated to {new_path}',
            'path': new_path
        }
    except Exception as e:
        logger.error(f"Error setting vault path: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def get_backup_directory() -> str:
    """Get directory for storing backup files"""
    backup_dir = os.path.join(FIDO_DATA_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def get_backup_history() -> Dict:
    """
    Get list of all backup files with metadata
    
    Returns:
        Dict with success status and list of backups
    """
    try:
        backup_dir = get_backup_directory()
        backups = []
        
        # Find all backup files
        for filename in os.listdir(backup_dir):
            if filename.startswith('vault_backup_') and filename.endswith('.json'):
                filepath = os.path.join(backup_dir, filename)
                stat_info = os.stat(filepath)
                
                # Extract timestamp from filename (format: vault_backup_YYYYMMDD_HHMMSS.json)
                timestamp_str = filename.replace('vault_backup_', '').replace('.json', '')
                try:
                    created_at = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                except ValueError:
                    created_at = datetime.fromtimestamp(stat_info.st_mtime)
                
                backups.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': stat_info.st_size,
                    'size_mb': round(stat_info.st_size / 1024 / 1024, 2),
                    'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': created_at.isoformat()
                })
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'success': True,
            'backups': backups,
            'count': len(backups),
            'backup_dir': backup_dir
        }
    
    except Exception as e:
        logger.exception("Error getting backup history")
        return {
            'success': False,
            'error': str(e),
            'backups': [],
            'count': 0
        }


def check_fido_binary() -> bool:
    """Check if virtual-fido binary exists and is executable"""
    return os.path.isfile(FIDO_BINARY) and os.access(FIDO_BINARY, os.X_OK)


def start_fido_device(passphrase: Optional[str] = None, vault_path: Optional[str] = None, verbose: bool = False) -> Dict:
    """
    Start virtual FIDO2 device
    
    Args:
        passphrase: Vault passphrase (default: 'passphrase')
        vault_path: Path to vault file (default: FIDO_VAULT_PATH)
        verbose: Enable verbose logging
    
    Returns:
        Dict with success status, pid, and message
    """
    if not check_fido_binary():
        return {
            'success': False,
            'error': f'FIDO binary not found at {FIDO_BINARY}'
        }
    
    try:
        cmd = [FIDO_BINARY, 'start']
        
        if passphrase:
            cmd.extend(['--passphrase', passphrase])
        else:
            cmd.extend(['--passphrase', get_fido_passphrase()])
        
        if vault_path:
            cmd.extend(['--vault', vault_path])
        else:
            cmd.extend(['--vault', FIDO_VAULT_PATH])
        
        if verbose:
            cmd.append('--verbose')
        
        logger.info(f"Starting FIDO device: {' '.join(cmd)}")
        
        # Start process in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Give it a moment to start
        import time
        time.sleep(0.5)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info(f"FIDO device started successfully, PID: {process.pid}")
            return {
                'success': True,
                'pid': process.pid,
                'message': 'FIDO device started successfully',
                'vault_path': vault_path or FIDO_VAULT_PATH
            }
        else:
            # Process died immediately
            stdout, stderr = process.communicate()
            error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
            logger.error(f"FIDO device failed to start: {error_msg}")
            return {
                'success': False,
                'error': f'Failed to start: {error_msg}',
                'stdout': stdout.decode('utf-8') if stdout else ''
            }
    
    except Exception as e:
        logger.exception("Error starting FIDO device")
        return {
            'success': False,
            'error': str(e)
        }


def stop_fido_device() -> Dict:
    """
    Stop virtual FIDO2 device
    
    Returns:
        Dict with success status and message
    """
    try:
        # Find and kill the process
        # First try to find by name
        find_cmd = ['pgrep', '-f', 'virtual-fido.*start']
        result = subprocess.run(find_cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]  # Get first PID
            
            # Kill the process
            kill_cmd = ['kill', pid]
            kill_result = subprocess.run(kill_cmd, capture_output=True, text=True)
            
            if kill_result.returncode == 0:
                logger.info(f"FIDO device stopped (PID: {pid})")
                return {
                    'success': True,
                    'message': f'FIDO device stopped (PID: {pid})',
                    'pid': pid
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to kill process {pid}: {kill_result.stderr}'
                }
        else:
            logger.warning("FIDO device not running")
            return {
                'success': True,
                'message': 'FIDO device was not running',
                'was_running': False
            }
    
    except Exception as e:
        logger.exception("Error stopping FIDO device")
        return {
            'success': False,
            'error': str(e)
        }


def get_fido_status() -> Dict:
    """
    Get virtual FIDO2 device status
    
    Returns:
        Dict with running status, pid, uptime
    """
    try:
        # Check if process is running
        cmd = ['pgrep', '-f', 'virtual-fido.*start']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]
            
            # Get process start time (uptime)
            ps_cmd = ['ps', '-p', pid, '-o', 'etime=']
            ps_result = subprocess.run(ps_cmd, capture_output=True, text=True)
            uptime = ps_result.stdout.strip() if ps_result.returncode == 0 else 'unknown'
            
            return {
                'is_running': True,
                'pid': int(pid),
                'uptime': uptime,
                'vault_path': FIDO_VAULT_PATH
            }
        else:
            return {
                'is_running': False,
                'pid': None,
                'uptime': None
            }
    
    except Exception as e:
        logger.exception("Error getting FIDO status")
        return {
            'is_running': False,
            'error': str(e)
        }


def list_fido_credentials(passphrase: Optional[str] = None, vault_path: Optional[str] = None) -> Dict:
    """
    List all credentials (identities) stored in vault
    
    Args:
        passphrase: Vault passphrase (default: DEFAULT_PASSPHRASE)
        vault_path: Path to vault file (default: FIDO_VAULT_PATH)
    
    Returns:
        Dict with success status and list of credentials
    """
    if not check_fido_binary():
        return {
            'success': False,
            'error': f'FIDO binary not found at {FIDO_BINARY}'
        }
    
    try:
        cmd = [FIDO_BINARY, 'list']
        
        if passphrase:
            cmd.extend(['--passphrase', passphrase])
        else:
            cmd.extend(['--passphrase', get_fido_passphrase()])
        
        if vault_path:
            cmd.extend(['--vault', vault_path])
        else:
            cmd.extend(['--vault', FIDO_VAULT_PATH])
        
        logger.debug(f"Listing credentials: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            logger.error(f"Failed to list credentials: {result.stderr}")
            return {
                'success': False,
                'error': result.stderr or 'Failed to list credentials'
            }
        
        # Parse output
        credentials = parse_credential_list(result.stdout)
        
        logger.info(f"Found {len(credentials)} credentials")
        return {
            'success': True,
            'credentials': credentials,
            'count': len(credentials)
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out'
        }
    except Exception as e:
        logger.exception("Error listing credentials")
        return {
            'success': False,
            'error': str(e)
        }


def delete_fido_credential(credential_id: str, passphrase: Optional[str] = None, vault_path: Optional[str] = None) -> Dict:
    """
    Delete a credential from vault
    
    Args:
        credential_id: ID of credential to delete
        passphrase: Vault passphrase (default: DEFAULT_PASSPHRASE)
        vault_path: Path to vault file (default: FIDO_VAULT_PATH)
    
    Returns:
        Dict with success status and message
    """
    if not check_fido_binary():
        return {
            'success': False,
            'error': f'FIDO binary not found at {FIDO_BINARY}'
        }
    
    if not credential_id:
        return {
            'success': False,
            'error': 'Credential ID is required'
        }
    
    try:
        cmd = [FIDO_BINARY, 'delete', credential_id]
        
        if passphrase:
            cmd.extend(['--passphrase', passphrase])
        else:
            cmd.extend(['--passphrase', get_fido_passphrase()])
        
        if vault_path:
            cmd.extend(['--vault', vault_path])
        else:
            cmd.extend(['--vault', FIDO_VAULT_PATH])
        
        logger.info(f"Deleting credential: {credential_id}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.info(f"Credential deleted successfully: {credential_id}")
            return {
                'success': True,
                'message': f'Credential {credential_id} deleted successfully',
                'credential_id': credential_id
            }
        else:
            logger.error(f"Failed to delete credential: {result.stderr}")
            return {
                'success': False,
                'error': result.stderr or 'Failed to delete credential'
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out'
        }
    except Exception as e:
        logger.exception("Error deleting credential")
        return {
            'success': False,
            'error': str(e)
        }


def parse_credential_list(output: str) -> List[Dict]:
    """
    Parse output from 'list' command
    
    Example output format:
    ------- Identities in file '/path/to/vault.json' -------
    ID: abc123
    Relying Party: example.com
    User: user@example.com
    Created: 2025-10-25
    --------
    
    Args:
        output: Raw stdout from list command
    
    Returns:
        List of credential dicts
    """
    credentials = []
    
    try:
        # Split by separator lines
        lines = output.strip().split('\n')
        
        current_cred = {}
        
        for line in lines:
            line = line.strip()
            
            # Skip header and separator lines
            if line.startswith('---') or not line or line.startswith('[LOG]'):
                if current_cred:
                    credentials.append(current_cred)
                    current_cred = {}
                continue
            
            # Parse key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                current_cred[key] = value
        
        # Add last credential
        if current_cred:
            credentials.append(current_cred)
        
    except Exception as e:
        logger.exception(f"Error parsing credential list: {e}")
    
    return credentials


def get_vault_info(vault_path: Optional[str] = None) -> Dict:
    """
    Get information about vault file
    
    Args:
        vault_path: Path to vault file (default: FIDO_VAULT_PATH)
    
    Returns:
        Dict with vault info (exists, size, modified time)
    """
    path = vault_path or FIDO_VAULT_PATH
    
    try:
        if os.path.exists(path):
            stat = os.stat(path)
            return {
                'exists': True,
                'path': path,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK)
            }
        else:
            return {
                'exists': False,
                'path': path
            }
    except Exception as e:
        return {
            'exists': False,
            'error': str(e)
        }


def backup_vault(backup_path: Optional[str] = None, vault_path: Optional[str] = None) -> Dict:
    """
    Create backup of vault file
    
    Args:
        backup_path: Path for backup file (auto-generated if not provided)
        vault_path: Path to vault file (default: current vault path from env)
    
    Returns:
        Dict with success status and backup_path
    """
    import shutil
    
    source = vault_path or get_vault_path()
    
    # Auto-generate backup path if not provided
    if not backup_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = get_backup_directory()
        backup_path = os.path.join(backup_dir, f'vault_backup_{timestamp}.json')
    
    try:
        # Check if vault file exists
        if not os.path.exists(source):
            return {
                'success': False,
                'error': f'Vault file not found: {source}'
            }
        
        # Check if vault file is not empty
        file_size = os.path.getsize(source)
        if file_size == 0:
            return {
                'success': False,
                'error': 'Vault file is empty. Cannot create backup of empty vault.'
            }
        
        # Check if device is running (warn but don't block)
        status = get_fido_status()
        if status.get('running', False):
            logger.warning("FIDO device is running during backup. Data may not be fully flushed.")
        
        shutil.copy2(source, backup_path)
        
        # Get file size
        file_size = os.path.getsize(backup_path)
        
        logger.info(f"Vault backed up: {source} -> {backup_path}")
        return {
            'success': True,
            'message': f'Vault backed up successfully',
            'source': source,
            'backup': backup_path,
            'filename': os.path.basename(backup_path),
            'size': file_size,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    except Exception as e:
        logger.exception("Error backing up vault")
        return {
            'success': False,
            'error': str(e)
        }


def restore_vault(backup_path: str, vault_path: Optional[str] = None) -> Dict:
    """
    Restore vault from backup
    
    IMPORTANT: This function will stop the FIDO device if running,
    restore the vault file, and provide instructions to restart.
    
    Args:
        backup_path: Path to backup file (or just filename if in backup directory)
        vault_path: Path to vault file (default: current vault path from env)
    
    Returns:
        Dict with success status and restart instructions
    """
    import shutil
    
    destination = vault_path or get_vault_path()
    
    # If backup_path is just a filename, look in backup directory
    if not os.path.dirname(backup_path):
        backup_dir = get_backup_directory()
        backup_path = os.path.join(backup_dir, backup_path)
    
    try:
        # Validate backup file exists
        if not os.path.exists(backup_path):
            return {
                'success': False,
                'error': f'Backup file not found: {backup_path}'
            }
        
        # Validate backup file is not empty
        backup_size = os.path.getsize(backup_path)
        if backup_size == 0:
            return {
                'success': False,
                'error': 'Backup file is empty. Cannot restore from empty backup.'
            }
        
        # Stop FIDO device if running (required for safe restore)
        device_was_running = False
        status = get_fido_status()
        if status.get('running', False):
            device_was_running = True
            logger.info("Stopping FIDO device for safe vault restore...")
            stop_result = stop_fido_device()
            if not stop_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Failed to stop FIDO device before restore. Restore aborted for safety.'
                }
        
        # Create backup of current vault if exists
        if os.path.exists(destination):
            temp_backup = f"{destination}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(destination, temp_backup)
            logger.info(f"Current vault backed up to: {temp_backup}")
        
        # Restore vault file
        shutil.copy2(backup_path, destination)
        
        logger.info(f"Vault restored: {backup_path} -> {destination}")
        
        return {
            'success': True,
            'message': f'Vault restored successfully',
            'backup': backup_path,
            'destination': destination,
            'filename': os.path.basename(backup_path),
            'device_was_running': device_was_running,
            'restart_required': device_was_running,
            'note': 'Device was stopped for safe restore. Please restart device to use restored credentials.' if device_was_running else 'Vault restored successfully.'
        }
    
    except Exception as e:
        logger.exception("Error restoring vault")
        return {
            'success': False,
            'error': str(e)
        }


def delete_backup(backup_filename: str) -> Dict:
    """
    Delete a backup file
    
    SECURITY: Only deletes files from backup directory. Path traversal is blocked.
    
    Args:
        backup_filename: Filename of backup to delete (no path separators allowed)
        
    Returns:
        Dict with success status
    """
    try:
        # SECURITY: Validate filename to prevent path traversal attacks
        if not backup_filename:
            return {
                'success': False,
                'error': 'Backup filename is required'
            }
        
        # Block path traversal attempts (../, ..\, absolute paths)
        if '/' in backup_filename or '\\' in backup_filename or backup_filename.startswith('.'):
            logger.warning(f"Path traversal attempt blocked: {backup_filename}")
            return {
                'success': False,
                'error': 'Invalid filename. Path separators and hidden files not allowed.'
            }
        
        # Construct safe path within backup directory
        backup_dir = get_backup_directory()
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # SECURITY: Verify final path is within backup directory (double-check)
        real_backup_dir = os.path.realpath(backup_dir)
        real_backup_path = os.path.realpath(backup_path)
        
        if not real_backup_path.startswith(real_backup_dir):
            logger.error(f"Path traversal blocked: {backup_filename} resolves outside backup directory")
            return {
                'success': False,
                'error': 'Invalid backup file path'
            }
        
        # Check if file exists
        if not os.path.exists(backup_path):
            return {
                'success': False,
                'error': f'Backup file not found: {backup_filename}'
            }
        
        # Check if it's actually a file (not directory)
        if not os.path.isfile(backup_path):
            return {
                'success': False,
                'error': f'Not a file: {backup_filename}'
            }
        
        # Delete the file
        os.remove(backup_path)
        logger.info(f"Backup deleted: {backup_path}")
        
        return {
            'success': True,
            'message': f'Backup {backup_filename} deleted successfully'
        }
    
    except Exception as e:
        logger.exception("Error deleting backup")
        return {
            'success': False,
            'error': str(e)
        }


# Quick test function
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== FIDO Utils Test ===\n")
    
    print("1. Checking binary...")
    print(f"Binary exists: {check_fido_binary()}")
    
    print("\n2. Getting status...")
    status = get_fido_status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    print("\n3. Listing credentials...")
    creds = list_fido_credentials()
    print(f"Credentials: {json.dumps(creds, indent=2)}")
    
    print("\n4. Vault info...")
    vault_info = get_vault_info()
    print(f"Vault: {json.dumps(vault_info, indent=2)}")
