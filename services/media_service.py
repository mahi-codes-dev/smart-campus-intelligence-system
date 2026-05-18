"""
Media Upload & File Management Service
Handles file uploads, validation, storage, and retrieval
"""

import os
import logging
import mimetypes
import uuid
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from database import get_db_connection

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = Path(__file__).resolve().parent.parent / "uploads"
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx', 'xls',
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    'mp4', 'avi', 'mov', 'mkv'
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 1024 * 1024  # 1MB

# Create upload folder if it doesn't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)

@contextmanager
def _connection_scope(connection=None):
    """Context manager for database connection."""
    if connection:
        yield connection
    else:
        with get_db_connection() as conn:
            yield conn

def ensure_media_table(connection=None):
    """Create media table if it doesn't exist."""
    with _connection_scope(connection) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS media (
                    id SERIAL PRIMARY KEY,
                    file_id UUID UNIQUE NOT NULL,
                    student_id INTEGER,
                    faculty_id INTEGER,
                    original_filename VARCHAR(255) NOT NULL,
                    stored_filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50),
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    upload_path TEXT,
                    description TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(student_id) REFERENCES students(id),
                    FOREIGN KEY(faculty_id) REFERENCES users(id)
                )
            """)
            
            # Add indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_file_id ON media(file_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_student_id ON media(student_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_faculty_id ON media(faculty_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_created_at ON media(created_at)
            """)

def is_file_allowed(filename):
    """Check if file type is allowed."""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_file(file_obj):
    """
    Validate file before upload.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_obj or file_obj.filename == '':
        return False, "No file provided"
    
    if not is_file_allowed(file_obj.filename):
        return False, f"File type not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    
    # Check file size
    file_obj.seek(0, os.SEEK_END)
    file_size = file_obj.tell()
    file_obj.seek(0)
    
    if file_size == 0:
        return False, "File is empty"
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
    
    return True, None

def save_file(file_obj, user_id=None, user_type='student'):
    """
    Save uploaded file and record in database.
    
    Args:
        file_obj: Flask FileStorage object
        user_id: ID of uploading user
        user_type: 'student' or 'faculty'
    
    Returns:
        dict: File metadata or None if failed
    """
    is_valid, error = validate_file(file_obj)
    if not is_valid:
        return {"success": False, "error": error}
    
    try:
        # Generate unique filename
        original_filename = secure_filename(file_obj.filename)
        file_id = uuid.uuid4()
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{file_id}.{file_ext}"
        
        # Save file
        file_path = UPLOAD_FOLDER / stored_filename
        file_obj.save(str(file_path))
        
        # Get file size
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        
        # Save metadata to database
        with _connection_scope() as conn:
            with conn.cursor() as cur:
                if user_type == 'student':
                    cur.execute("""
                        INSERT INTO media (
                            file_id, student_id, original_filename, stored_filename,
                            file_type, file_size, mime_type, upload_path
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(file_id),
                        user_id,
                        original_filename,
                        stored_filename,
                        file_ext,
                        file_size,
                        mime_type,
                        str(file_path)
                    ))
                else:  # faculty
                    cur.execute("""
                        INSERT INTO media (
                            file_id, faculty_id, original_filename, stored_filename,
                            file_type, file_size, mime_type, upload_path
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(file_id),
                        user_id,
                        original_filename,
                        stored_filename,
                        file_ext,
                        file_size,
                        mime_type,
                        str(file_path)
                    ))
            
            conn.commit()
        
        logger.info(f"File uploaded: {stored_filename} by {user_type} {user_id}")
        
        return {
            "success": True,
            "file_id": str(file_id),
            "filename": original_filename,
            "size": file_size,
            "type": file_ext,
            "mime_type": mime_type
        }
    
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        return {"success": False, "error": str(e)}

def get_file_by_id(file_id, user_id=None, user_type='student'):
    """Retrieve file metadata from database."""
    try:
        with _connection_scope() as conn:
            with conn.cursor() as cur:
                if user_type == 'student':
                    cur.execute("""
                        SELECT id, file_id, original_filename, stored_filename,
                               file_type, file_size, mime_type, upload_path,
                               created_at, is_public
                        FROM media
                        WHERE file_id = %s AND (student_id = %s OR is_public = TRUE)
                    """, (file_id, user_id))
                else:  # faculty
                    cur.execute("""
                        SELECT id, file_id, original_filename, stored_filename,
                               file_type, file_size, mime_type, upload_path,
                               created_at, is_public
                        FROM media
                        WHERE file_id = %s AND (faculty_id = %s OR is_public = TRUE)
                    """, (file_id, user_id))
                
                result = cur.fetchone()
                if result:
                    return {
                        "id": result[0],
                        "file_id": result[1],
                        "original_filename": result[2],
                        "stored_filename": result[3],
                        "file_type": result[4],
                        "file_size": result[5],
                        "mime_type": result[6],
                        "upload_path": result[7],
                        "created_at": result[8],
                        "is_public": result[9]
                    }
        
        return None
    
    except Exception as e:
        logger.error(f"Error retrieving file: {str(e)}")
        return None

def list_user_files(user_id, user_type='student', limit=50, offset=0):
    """List files uploaded by a user."""
    try:
        with _connection_scope() as conn:
            with conn.cursor() as cur:
                if user_type == 'student':
                    cur.execute("""
                        SELECT id, file_id, original_filename, file_type,
                               file_size, created_at
                        FROM media
                        WHERE student_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, limit, offset))
                else:  # faculty
                    cur.execute("""
                        SELECT id, file_id, original_filename, file_type,
                               file_size, created_at
                        FROM media
                        WHERE faculty_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, limit, offset))
                
                results = cur.fetchall()
                return [
                    {
                        "id": row[0],
                        "file_id": row[1],
                        "filename": row[2],
                        "type": row[3],
                        "size": row[4],
                        "created_at": row[5]
                    }
                    for row in results
                ]
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return []

def delete_file(file_id, user_id, user_type='student'):
    """Delete file from storage and database."""
    try:
        # Get file info
        file_info = get_file_by_id(file_id, user_id, user_type)
        if not file_info:
            return {"success": False, "error": "File not found or access denied"}
        
        # Delete from filesystem
        file_path = file_info.get("upload_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        with _connection_scope() as conn:
            with conn.cursor() as cur:
                if user_type == 'student':
                    cur.execute("""
                        DELETE FROM media
                        WHERE file_id = %s AND student_id = %s
                    """, (file_id, user_id))
                else:
                    cur.execute("""
                        DELETE FROM media
                        WHERE file_id = %s AND faculty_id = %s
                    """, (file_id, user_id))
            
            conn.commit()
        
        logger.info(f"File deleted: {file_id}")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return {"success": False, "error": str(e)}

def make_file_public(file_id, user_id, user_type='student', is_public=True):
    """Toggle file public/private status."""
    try:
        with _connection_scope() as conn:
            with conn.cursor() as cur:
                if user_type == 'student':
                    cur.execute("""
                        UPDATE media
                        SET is_public = %s
                        WHERE file_id = %s AND student_id = %s
                    """, (is_public, file_id, user_id))
                else:
                    cur.execute("""
                        UPDATE media
                        SET is_public = %s
                        WHERE file_id = %s AND faculty_id = %s
                    """, (is_public, file_id, user_id))
            
            conn.commit()
        
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error updating file: {str(e)}")
        return {"success": False, "error": str(e)}

_MEDIA_SCHEMA_READY = False

def initialize_media():
    """Initialize media service on app startup."""
    global _MEDIA_SCHEMA_READY
    if not _MEDIA_SCHEMA_READY:
        ensure_media_table()
        _MEDIA_SCHEMA_READY = True
