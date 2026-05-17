"""
Supabase Storage helpers for uploading images and generating signed URLs.

All photo assets (profile photos, haircut posts, gallery images) are stored
in a single Supabase Storage bucket. This module wraps the supabase-py client
with two public functions:

- :func:`sign_storage_path` — convert a storage path to a time-limited URL.
- :func:`upload_photo_to_storage` — upload raw image bytes and return the path.
"""

import os
import mimetypes
from supabase import create_client

_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _supabase = create_client(url, key)
    return _supabase

def sign_storage_path(path: str, expires_in: int = 3600) -> str | None:
    """
    Given a storage path like 'barber_12/photo_987.jpg', returns a signed URL.
    """
    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "haircuts")
    if not path:
        return None

    sb = get_supabase()
    res = sb.storage.from_(bucket).create_signed_url(path, expires_in)

    # supabase-py returns a dict-like object; support both shapes
    if isinstance(res, dict):
        return res.get("signedURL") or res.get("signedUrl") or res.get("signed_url")
    return getattr(res, "signed_url", None) or getattr(res, "signedURL", None)

def upload_photo_to_storage(barber_id: int, file_data: bytes, filename: str) -> str | None:
    """
    Upload a photo to Supabase storage and return the storage path.
    
    Args:
        barber_id: The barber's ID
        file_data: The file content as bytes
        filename: Original filename (used to get extension)
    
    Returns:
        Storage path (e.g., 'barber_12/photo_123.jpg') or None if upload fails
    """
    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "haircuts")
    if not file_data:
        return None
    
    # Generate storage path: barber_<id>/<uuid>.<ext>
    import uuid
    file_ext = os.path.splitext(filename)[1].lower()
    storage_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = f"barber_{barber_id}/{storage_filename}"
    
    # Determine MIME type from file extension
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        # Default to common image types based on extension
        mime_mapping = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_mapping.get(file_ext, 'application/octet-stream')
    
    print(f"[UPLOAD_PHOTO] Uploading {filename} (MIME: {mime_type}) to {storage_path}")
    print(f"[UPLOAD_PHOTO] Bucket: {bucket}, Barber ID: {barber_id}, File size: {len(file_data)} bytes")
    
    try:
        sb = get_supabase()
        
        # Ensure the barber folder path exists by attempting upload with proper metadata
        print(f"[UPLOAD_PHOTO] Attempting upload with contentType in file_options")
        
        # Try uploading with file_options parameter (content-type)
        try:
            res = sb.storage.from_(bucket).upload(
                storage_path, 
                file_data,
                file_options={"content-type": mime_type}
            )
            print(f"[UPLOAD_PHOTO] Upload with file_options succeeded. Response: {res}")
            if res:
                return storage_path
        except TypeError as te:
            # If file_options parameter doesn't exist, try without it
            print(f"[UPLOAD_PHOTO] file_options parameter not supported: {te}")
            print(f"[UPLOAD_PHOTO] Attempting upload without file_options")
            
            res = sb.storage.from_(bucket).upload(storage_path, file_data)
            print(f"[UPLOAD_PHOTO] Upload without file_options response: {res}")
            if res:
                return storage_path
        
        return None
        
    except Exception as e:
        print(f"[UPLOAD_PHOTO] Error uploading to Supabase: {e}")
        print(f"[UPLOAD_PHOTO] Error type: {type(e).__name__}")
        import traceback
        print(f"[UPLOAD_PHOTO] Traceback: {traceback.format_exc()}")
        
        # Log additional debug info
        print(f"[UPLOAD_PHOTO] Debug info:")
        print(f"  - Storage path: {storage_path}")
        print(f"  - MIME type: {mime_type}")
        print(f"  - File extension: {file_ext}")
        print(f"  - File data length: {len(file_data)}")
        
        return None