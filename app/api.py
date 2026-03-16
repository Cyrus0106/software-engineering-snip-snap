from datetime import datetime
from flask import Blueprint, request, jsonify, session

from .db import fetch_discover_posts, fetch_discover_search_items, get_user_location
from .supabase_storage import sign_storage_path

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/discover/search_items")
def discover_search_items():
    items = fetch_discover_search_items()
    return jsonify({"items": items})


def _parse_cursor(cursor_value: str):
    """
    Expects cursor like: "2026-03-04T16:32:36.123456Z|123"
    Returns (datetime, int) or None
    """
    if not cursor_value:
        return None
    try:
        created_at_s, photo_id_s = cursor_value.split("|", 1)
        # Accept Z or no Z
        created_at_s = created_at_s.replace("Z", "")
        dt = datetime.fromisoformat(created_at_s)
        return (dt, int(photo_id_s))
    except Exception:
        return None


def _make_next_cursor(items):
    """
    items from fetch_discover_posts are RealDictCursor dicts containing
    created_at + photo_id.
    """
    if not items:
        return None
    last = items[-1]
    created_at = last.get("created_at")
    photo_id = last.get("photo_id")
    if not created_at or photo_id is None:
        return None
    # created_at is already a datetime from psycopg2
    return f"{created_at.isoformat()}Z|{int(photo_id)}"


@api_bp.post("/gallery/posts")
def gallery_posts():
    payload = request.get_json(silent=True) or {}

    tag_ids = payload.get("tag_ids") or []
    barber_ids = payload.get("barber_ids") or []
    barbershop_ids = payload.get("barbershop_ids") or []
    effective_sort = (payload.get("effective_sort") or "most_recent").strip().lower()
    limit = int(payload.get("limit") or 18)

    cursor_raw = payload.get("cursor")
    cursor = _parse_cursor(cursor_raw) if isinstance(cursor_raw, str) else None

    # --- viewer location (customer OR barber) ---
    u = session.get("user") or {}
    uid = u.get("id")

    viewer_lat = None
    viewer_lng = None

    if uid is not None:
        loc = get_user_location(int(uid))  # returns {"lat": float, "lng": float} or None
        if loc:
            viewer_lat = loc["lat"]
            viewer_lng = loc["lng"]

    print("gallery_posts effective_sort =", effective_sort, "viewer_lat/lng =", viewer_lat, viewer_lng)

    # Fetch 1 extra so we can calculate has_more
    rows = fetch_discover_posts(
        tag_ids=tag_ids,
        barber_ids=barber_ids,
        barbershop_ids=barbershop_ids,
        cursor=cursor,
        limit=limit + 1,
        effective_sort=effective_sort,
        viewer_lat=viewer_lat,
        viewer_lng=viewer_lng,
    )

    has_more = len(rows) > limit
    items = rows[:limit]
    for it in items:
        # Haircut photo
        it["image_url"] = sign_storage_path(it.get("image_url"), expires_in=3600)

        # Promo profile photo (optional)
        it["promo_profile_image_url"] = sign_storage_path(
            it.get("promo_profile_image_url"), expires_in=3600
        )

    next_cursor = _make_next_cursor(items) if has_more else None

    return jsonify(
        {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    )