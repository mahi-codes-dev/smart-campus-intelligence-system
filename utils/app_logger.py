"""
Debugging Support: Centralized logging for backend operations.
Tracks API requests, database operations, and data transformations.
"""

import logging
import sys
from functools import wraps
from flask import request, jsonify
import json
from datetime import datetime

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app_logs.log")
    ]
)

logger = logging.getLogger(__name__)


def log_request(f):
    """Decorator to log API requests and responses."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Log request details
        logger.info(f"📨 API Request: {request.method} {request.path}")
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                logger.info(f"📄 Request Body: {json.dumps(request.json, indent=2) if request.json else 'N/A'}")
            except Exception as e:
                logger.warning(f"Unable to log request body: {str(e)}")
        
        # Execute the function
        response = f(*args, **kwargs)
        
        # Log response
        if isinstance(response, tuple):
            status_code = response[1] if len(response) > 1 else 200
        else:
            status_code = 200
        
        logger.info(f"✅ Response Status: {status_code}")
        
        return response
    
    return decorated


def log_database_operation(operation_type, table, details=None):
    """Log database operations."""
    timestamp = datetime.now().isoformat()
    log_entry = f"🗄️  DB Operation: {operation_type} on '{table}' at {timestamp}"
    if details:
        log_entry += f" | Details: {details}"
    logger.info(log_entry)


def log_calculation(metric_name, student_id, value, metadata=None):
    """Log calculated metrics."""
    log_entry = f"📊 Metric: {metric_name} | Student: {student_id} | Value: {value}"
    if metadata:
        log_entry += f" | Metadata: {metadata}"
    logger.info(log_entry)


def log_error(error_message, error_type=None, context=None):
    """Log errors with context."""
    log_entry = f"❌ Error: {error_message}"
    if error_type:
        log_entry += f" | Type: {error_type}"
    if context:
        log_entry += f" | Context: {context}"
    logger.error(log_entry)


def log_warning(warning_message, context=None):
    """Log warnings."""
    log_entry = f"⚠️  Warning: {warning_message}"
    if context:
        log_entry += f" | Context: {context}"
    logger.warning(log_entry)
