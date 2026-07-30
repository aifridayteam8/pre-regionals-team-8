import os
from werkzeug.datastructures import FileStorage
from flask import request


def validate_file(file: FileStorage) -> tuple:
    """Validate uploaded file."""
    if not file:
        return False, "No file provided"
    
    # Check file extension
    filename = file.filename
    if not filename:
        return False, "No filename provided"
    
    allowed_extensions = {'json', 'txt', 'csv', 'log'}
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if file_ext not in allowed_extensions:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size (16MB max)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    max_size = 16 * 1024 * 1024  # 16MB
    if file_size > max_size:
        return False, f"File too large. Maximum size: {max_size / (1024*1024)}MB"
    
    return True, "File valid"
