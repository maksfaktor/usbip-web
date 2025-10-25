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
    restore_vault
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
        
        # Get credentials list
        credentials = list_fido_credentials()
        
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
        credentials = list_fido_credentials()
        
        return jsonify({
            'success': True,
            'credentials': credentials,
            'count': len(credentials)
        })
        
    except Exception as e:
        logger.error(f"Error getting FIDO credentials: {e}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
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
