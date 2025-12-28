"""
FIDO2 Virtual Device Management Routes
Blueprint for virtual-fido device control and credential management
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import logging

from app import db
from models import FidoDevice, FidoCredential, FidoLog
from fido_utils import (
    check_fido_binary,
    get_fido_status,
    start_fido_device,
    stop_fido_device,
    list_fido_credentials,
    delete_fido_credential,
    get_vault_info,
    backup_vault,
    restore_vault,
    delete_backup,
    get_fido_passphrase,
    set_fido_passphrase,
    get_vault_path,
    set_vault_path,
    get_backup_history
)

logger = logging.getLogger(__name__)

# Create Blueprint
fido_bp = Blueprint('fido', __name__, url_prefix='/fido')


def log_fido_event(event_type, status, rp_id=None, credential_id=None, details=None):
    """Helper function to log FIDO events to database"""
    try:
        log_entry = FidoLog(
            event_type=event_type,
            status=status,
            rp_id=rp_id,
            credential_id=credential_id,
            details=details,
            ip_address=request.remote_addr if request else None,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(log_entry)
        db.session.commit()
        logger.debug(f"FIDO event logged: {event_type} - {status}")
    except Exception as e:
        logger.error(f"Failed to log FIDO event: {e}")
        db.session.rollback()


def get_or_create_fido_device():
    """Get existing FidoDevice or create new one"""
    device = FidoDevice.query.first()
    if not device:
        device = FidoDevice()
        db.session.add(device)
        db.session.commit()
        logger.info("Created new FidoDevice record")
    return device


@fido_bp.route('/help')
@login_required
def help_page():
    """FIDO2 help and instructions page"""
    return render_template('fido_help.html')


@fido_bp.route('/device')
@login_required
def device_page():
    """Main FIDO device management page"""
    try:
        # Get or create device record
        device = get_or_create_fido_device()
        
        # Check binary status
        binary_exists = check_fido_binary()
        
        # Get current device status
        status_info = get_fido_status()
        
        # Get vault info
        vault_info = get_vault_info()
        
        # Get credentials list (handle missing binary gracefully)
        credentials_result = list_fido_credentials()
        if credentials_result.get('success'):
            credentials = credentials_result.get('credentials', [])
        else:
            credentials = []
            logger.warning(f"Could not load credentials: {credentials_result.get('error')}")
        
        # Get recent logs
        recent_logs = FidoLog.query.order_by(FidoLog.timestamp.desc()).limit(10).all()
        
        return render_template(
            'fido_device.html',
            device=device,
            binary_exists=binary_exists,
            status_info=status_info,
            vault_info=vault_info,
            credentials=credentials,
            recent_logs=recent_logs
        )
    except Exception as e:
        logger.error(f"Error loading FIDO device page: {e}")
        flash(f"Error loading FIDO device page: {str(e)}", "danger")
        return redirect(url_for('index'))


@fido_bp.route('/start', methods=['POST'])
@login_required
def start_device():
    """Start FIDO virtual device"""
    try:
        device = get_or_create_fido_device()
        
        # Check if already running
        if device.is_running:
            return jsonify({
                'success': False,
                'message': 'FIDO device is already running',
                'pid': device.pid
            }), 400
        
        # Start device
        result = start_fido_device()
        
        if result['success']:
            # Update database
            device.is_running = True
            device.pid = result.get('pid')
            device.started_at = datetime.utcnow()
            device.last_error = None
            db.session.commit()
            
            # Log event
            log_fido_event('device_start', 'success', details=f"PID: {result.get('pid')}")
            
            flash('FIDO device started successfully!', 'success')
            return jsonify({
                'success': True,
                'message': 'FIDO device started successfully',
                'pid': result.get('pid')
            })
        else:
            # Update error
            device.last_error = result.get('error', 'Unknown error')
            db.session.commit()
            
            # Log event
            log_fido_event('device_start', 'failed', details=result.get('error'))
            
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to start FIDO device')
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting FIDO device: {e}")
        log_fido_event('device_start', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/stop', methods=['POST'])
@login_required
def stop_device():
    """Stop FIDO virtual device"""
    try:
        device = get_or_create_fido_device()
        
        # Check if not running
        if not device.is_running:
            return jsonify({
                'success': False,
                'message': 'FIDO device is not running'
            }), 400
        
        # Stop device
        result = stop_fido_device()
        
        if result['success']:
            # Update database
            device.is_running = False
            device.pid = None
            device.stopped_at = datetime.utcnow()
            device.last_error = None
            db.session.commit()
            
            # Log event
            log_fido_event('device_stop', 'success')
            
            flash('FIDO device stopped successfully!', 'success')
            return jsonify({
                'success': True,
                'message': 'FIDO device stopped successfully'
            })
        else:
            # Update error
            device.last_error = result.get('error', 'Unknown error')
            db.session.commit()
            
            # Log event
            log_fido_event('device_stop', 'failed', details=result.get('error'))
            
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to stop FIDO device')
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping FIDO device: {e}")
        log_fido_event('device_stop', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/status', methods=['GET'])
@login_required
def get_status():
    """Get current FIDO device status (API endpoint)"""
    try:
        device = get_or_create_fido_device()
        status_info = get_fido_status()
        
        # Update database if status changed
        if status_info['is_running'] != device.is_running:
            device.is_running = status_info['is_running']
            device.pid = status_info.get('pid')
            db.session.commit()
            logger.info(f"FIDO device status updated: running={device.is_running}, pid={device.pid}")
        
        return jsonify({
            'success': True,
            'status': {
                'running': device.is_running,
                'pid': device.pid,
                'started_at': device.started_at.isoformat() if device.started_at else None,
                'stopped_at': device.stopped_at.isoformat() if device.stopped_at else None,
                'last_error': device.last_error,
                'auto_start': device.auto_start
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting FIDO device status: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/credentials', methods=['GET'])
@login_required
def get_credentials():
    """Get list of FIDO credentials (API endpoint)"""
    try:
        result = list_fido_credentials()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'credentials': result.get('credentials', []),
                'count': result.get('count', 0)
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to list credentials'),
                'credentials': [],
                'count': 0
            })
        
    except Exception as e:
        logger.error(f"Error getting FIDO credentials: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}",
            'credentials': [],
            'count': 0
        }), 500


@fido_bp.route('/credentials/<credential_id>', methods=['DELETE'])
@login_required
def delete_credential(credential_id):
    """Delete a FIDO credential"""
    try:
        result = delete_fido_credential(credential_id)
        
        if result['success']:
            # Log event
            log_fido_event('credential_delete', 'success', credential_id=credential_id)
            
            # Delete from database if exists
            db_credential = FidoCredential.query.filter_by(credential_id=credential_id).first()
            if db_credential:
                db.session.delete(db_credential)
                db.session.commit()
            
            flash('Credential deleted successfully!', 'success')
            return jsonify({
                'success': True,
                'message': 'Credential deleted successfully'
            })
        else:
            # Log event
            log_fido_event('credential_delete', 'failed', credential_id=credential_id, details=result.get('error'))
            
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to delete credential')
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting FIDO credential: {e}")
        log_fido_event('credential_delete', 'failed', credential_id=credential_id, details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/logs', methods=['GET'])
@login_required
def get_logs():
    """Get FIDO operation logs (API endpoint)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        event_type = request.args.get('event_type', None)
        
        query = FidoLog.query
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        logs = query.order_by(FidoLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs],
            'count': len(logs)
        })
        
    except Exception as e:
        logger.error(f"Error getting FIDO logs: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/passphrase/get', methods=['GET'])
@login_required
def get_passphrase_status():
    """Get current passphrase status (not the actual value for security)"""
    try:
        current = get_fido_passphrase()
        is_default = (current == 'passphrase')
        
        return jsonify({
            'success': True,
            'is_default': is_default,
            'length': len(current),
            'masked': '*' * len(current)
        })
        
    except Exception as e:
        logger.error(f"Error getting passphrase status: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/passphrase/change', methods=['POST'])
@login_required
def change_passphrase():
    """Change FIDO passphrase"""
    try:
        data = request.get_json()
        new_passphrase = data.get('new_passphrase')
        
        if not new_passphrase:
            return jsonify({
                'success': False,
                'message': 'New passphrase is required'
            }), 400
        
        result = set_fido_passphrase(new_passphrase)
        
        if result['success']:
            flash('Passphrase updated successfully! Please restart device.', 'success')
            log_fido_event('passphrase_change', 'success')
            return jsonify(result)
        else:
            log_fido_event('passphrase_change', 'failed', details=result.get('error'))
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error changing passphrase: {e}")
        log_fido_event('passphrase_change', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/vault/backup', methods=['POST'])
@login_required
def backup_vault_route():
    """Create backup of FIDO vault"""
    try:
        result = backup_vault()
        
        if result['success']:
            log_fido_event('vault_backup', 'success', details=f"Backup: {result.get('backup')}")
            
            flash(f'Vault backup created: {result.get("backup")}', 'success')
            return jsonify({
                'success': True,
                'message': 'Vault backup created successfully',
                'backup_path': result.get('backup')
            })
        else:
            log_fido_event('vault_backup', 'failed', details=result.get('error'))
            
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to create backup')
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating vault backup: {e}")
        log_fido_event('vault_backup', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/vault/path', methods=['GET'])
@login_required
def get_vault_path_route():
    """Get current vault file path"""
    try:
        path = get_vault_path()
        return jsonify({
            'success': True,
            'path': path
        })
    except Exception as e:
        logger.error(f"Error getting vault path: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/vault/path', methods=['POST'])
@login_required
def set_vault_path_route():
    """Set new vault file path"""
    try:
        data = request.get_json()
        new_path = data.get('path')
        
        if not new_path:
            return jsonify({
                'success': False,
                'message': 'Path is required'
            }), 400
        
        result = set_vault_path(new_path)
        
        if result['success']:
            log_fido_event('vault_path_change', 'success', details=new_path)
            flash(f'Vault path updated to: {new_path}', 'success')
        else:
            log_fido_event('vault_path_change', 'failed', details=result.get('error'))
            
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error setting vault path: {e}")
        log_fido_event('vault_path_change', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/vault/backups', methods=['GET'])
@login_required
def get_backups_route():
    """Get list of all backup files"""
    try:
        result = get_backup_history()
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error getting backup history: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}",
            'backups': [],
            'count': 0
        }), 500


@fido_bp.route('/vault/restore', methods=['POST'])
@login_required
def restore_vault_route():
    """Restore vault from backup"""
    try:
        data = request.get_json()
        backup_filename = data.get('backup_filename')
        
        if not backup_filename:
            return jsonify({
                'success': False,
                'message': 'Backup filename is required'
            }), 400
        
        result = restore_vault(backup_filename)
        
        if result['success']:
            log_fido_event('vault_restore', 'success', details=f"From: {backup_filename}")
            flash(f'Vault restored from backup: {backup_filename}', 'success')
        else:
            log_fido_event('vault_restore', 'failed', details=result.get('error'))
            
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error restoring vault: {e}")
        log_fido_event('vault_restore', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/vault/backup/<filename>', methods=['DELETE'])
@login_required
def delete_backup_route(filename):
    """Delete a backup file"""
    try:
        result = delete_backup(filename)
        
        if result['success']:
            log_fido_event('backup_delete', 'success', details=filename)
            flash(f'Backup deleted: {filename}', 'success')
        else:
            log_fido_event('backup_delete', 'failed', details=result.get('error'))
            
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error deleting backup: {e}")
        log_fido_event('backup_delete', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/vault/backup/<filename>/download', methods=['GET'])
@login_required
def download_backup_route(filename):
    """Download a backup file"""
    try:
        from flask import send_file
        from fido_utils import get_backup_directory
        import os
        
        backup_dir = get_backup_directory()
        backup_path = os.path.join(backup_dir, filename)
        
        if not os.path.exists(backup_path):
            flash(f'Backup file not found: {filename}', 'error')
            return jsonify({
                'success': False,
                'message': f'Backup file not found: {filename}'
            }), 404
        
        log_fido_event('backup_download', 'success', details=filename)
        return send_file(backup_path, as_attachment=True, download_name=filename)
            
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        log_fido_event('backup_download', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/vault/download', methods=['GET'])
@login_required
def download_vault_route():
    """Download current vault.json file for backup"""
    try:
        from flask import send_file
        from fido_utils import FIDO_VAULT_PATH
        import os
        from datetime import datetime
        
        if not os.path.exists(FIDO_VAULT_PATH):
            flash('Vault file not found', 'error')
            return jsonify({
                'success': False,
                'message': 'Vault file not found'
            }), 404
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f'vault_backup_{timestamp}.json'
        
        log_fido_event('vault_download', 'success', details='Current vault downloaded')
        return send_file(FIDO_VAULT_PATH, as_attachment=True, download_name=download_name)
            
    except Exception as e:
        logger.error(f"Error downloading vault: {e}")
        log_fido_event('vault_download', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/logs', methods=['GET'])
@login_required
def get_logs_route():
    """Get FIDO operation logs with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        event_type = request.args.get('event_type', None)
        status = request.args.get('status', None)
        
        # Build query
        query = FidoLog.query
        
        # Apply filters
        if event_type and event_type != 'all':
            query = query.filter_by(event_type=event_type)
        
        if status and status != 'all':
            query = query.filter_by(status=status)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(FidoLog.timestamp.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Format logs for JSON response
        logs = []
        for log in pagination.items:
            logs.append({
                'id': log.id,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A',
                'event_type': log.event_type,
                'status': log.status,
                'rp_id': log.rp_id,
                'credential_id': log.credential_id[:16] + '...' if log.credential_id and len(log.credential_id) > 16 else log.credential_id,
                'details': log.details,
                'ip_address': log.ip_address,
                'user_id': log.user_id
            })
        
        return jsonify({
            'success': True,
            'logs': logs,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}",
            'logs': []
        }), 500


@fido_bp.route('/logs/clear', methods=['POST'])
@login_required
def clear_logs_route():
    """Clear old FIDO logs"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 30)  # Default: clear logs older than 30 days
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old logs
        deleted_count = FidoLog.query.filter(FidoLog.timestamp < cutoff_date).delete()
        db.session.commit()
        
        logger.info(f"Cleared {deleted_count} logs older than {days} days")
        log_fido_event('logs_clear', 'success', details=f"Deleted {deleted_count} logs older than {days} days")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted_count} logs older than {days} days',
            'deleted_count': deleted_count
        })
    
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        db.session.rollback()
        log_fido_event('logs_clear', 'failed', details=str(e))
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500


@fido_bp.route('/logs/stats', methods=['GET'])
@login_required
def get_log_stats_route():
    """Get statistics about FIDO logs"""
    try:
        from sqlalchemy import func
        
        # Total logs count
        total_logs = FidoLog.query.count()
        
        # Count by event type
        event_counts = db.session.query(
            FidoLog.event_type,
            func.count(FidoLog.id).label('count')
        ).group_by(FidoLog.event_type).all()
        
        # Count by status
        status_counts = db.session.query(
            FidoLog.status,
            func.count(FidoLog.id).label('count')
        ).group_by(FidoLog.status).all()
        
        # Recent activity (last 24 hours)
        from datetime import datetime, timedelta
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_count = FidoLog.query.filter(FidoLog.timestamp >= last_24h).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_logs': total_logs,
                'recent_24h': recent_count,
                'by_event_type': {item[0]: item[1] for item in event_counts},
                'by_status': {item[0]: item[1] for item in status_counts}
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching log stats: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500
