import os
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