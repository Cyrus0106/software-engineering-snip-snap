import os
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

import psycopg2
import psycopg2.extras


def _get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    # Supabase Postgres requires SSL. Enforce if not present in the URL.
    if "sslmode=" not in db_url:
        sep = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{sep}sslmode=require"

    return psycopg2.connect(db_url)


def filter_existing_tag_ids(tag_ids: List[int]) -> List[int]:
    if not tag_ids:
        return []
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tag_id FROM Tag WHERE tag_id = ANY(%s)",
                (tag_ids,),
            )
            rows = cur.fetchall()
    return [r[0] for r in rows]


def create_haircut_post(barber_id: int, image_url: str, width_px: int, height_px: int, tag_ids: List[int]):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO HaircutPhoto (barber_id, image_url, width_px, height_px, is_post)
                VALUES (%s, %s, %s, %s, TRUE)
                RETURNING photo_id
                """,
                (barber_id, image_url, width_px, height_px),
            )
            photo_id = cur.fetchone()[0]

            for tag_id in tag_ids:
                cur.execute(
                    """
                    INSERT INTO HaircutPhoto_Tag (photo_id, tag_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (photo_id, tag_id),
                )
    return photo_id


def fetch_discover_posts(
    tag_ids: List[int],
    barber_ids: List[int],
    barbershop_ids: List[int],
    cursor: Optional[Tuple[datetime, int]],
    limit: int,
    effective_sort: str,
) -> List[Dict[str, Any]]:
    where = ["hp.is_post = TRUE", "hp.status = 'show'"]
    params: List[Any] = []

    join = []
    having = []

    if barbershop_ids:
        join.append("JOIN Barber b ON b.barber_id = hp.barber_id")
        where.append("b.barbershop_id = ANY(%s)")
        params.append(barbershop_ids)

    if barber_ids:
        where.append("hp.barber_id = ANY(%s)")
        params.append(barber_ids)

    if tag_ids:
        join.append("JOIN HaircutPhoto_Tag hpt ON hpt.photo_id = hp.photo_id")
        where.append("hpt.tag_id = ANY(%s)")
        params.append(tag_ids)
        having.append("COUNT(DISTINCT hpt.tag_id) = %s")
        params.append(len(tag_ids))

    if cursor is not None:
        cursor_created_at, cursor_photo_id = cursor
        where.append("(hp.created_at < %s OR (hp.created_at = %s AND hp.photo_id < %s))")
        params.extend([cursor_created_at, cursor_created_at, cursor_photo_id])

    order_by = "hp.created_at DESC, hp.photo_id DESC"

    if effective_sort == "closest":
        order_by = "hp.created_at DESC, hp.photo_id DESC"

    if effective_sort == "highest_rated":
        order_by = "hp.created_at DESC, hp.photo_id DESC"

    having_sql = f"HAVING {' AND '.join(having)}" if having else ""

    sql = f"""
        SELECT hp.photo_id, hp.image_url, hp.width_px, hp.height_px, hp.created_at
        FROM HaircutPhoto hp
        {' '.join(join)}
        WHERE {' AND '.join(where)}
        GROUP BY hp.photo_id
        {having_sql}
        ORDER BY {order_by}
        LIMIT %s
    """
    params.append(limit)

    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return rows


def _pick_label(row: Dict[str, Any], preferred_keys: List[str]) -> str:
    for k in preferred_keys:
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for k, v in row.items():
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def get_user_promo(user_id: int) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    u.user_id,
                    u.username AS name,
                    u.role,
                    pp.image_url AS profile_image_url,
                    bs.name AS barbershop_name
                FROM App_User u
                LEFT JOIN Barber b ON b.user_id = u.user_id
                LEFT JOIN Barbershop bs ON bs.barbershop_id = b.barbershop_id
                LEFT JOIN ProfilePhoto pp ON pp.user_id = u.user_id
                WHERE u.user_id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()

    if not row:
        return None

    raw_url = row.get("profile_image_url")
    image_url = None
    if raw_url and "/profiles/" in raw_url:
        image_url = raw_url.replace("/static/uploads/profiles/", "/static/uploads/profile_photos/")
    elif raw_url:
        image_url = raw_url

    return {
        "name": row.get("name") or "Unknown",
        "role": row.get("role") or "",
        "profile_image_url": image_url,
        "barbershop_name": row.get("barbershop_name") or "",
    }


import psycopg2.extras


def get_barbershops_for_map():
    """Return all barbershops with their barbers for the map page API."""
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    bs.barbershop_id,
                    bs.name,
                    bs.postcode,
                    bs.location_lat,
                    bs.location_lng,
                    bs.phone,
                    bs.website,
                    b.barber_id,
                    b.bio,
                    u.username,
                    pp.image_url AS profile_image_url
                FROM Barbershop bs
                LEFT JOIN Barber b ON b.barbershop_id = bs.barbershop_id
                LEFT JOIN App_User u ON u.user_id = b.user_id
                LEFT JOIN ProfilePhoto pp ON pp.user_id = b.user_id
                ORDER BY bs.barbershop_id, b.barber_id
                """
            )
            rows = cur.fetchall()

    shops = {}
    for row in rows:
        bid = row["barbershop_id"]
        if bid not in shops:
            shops[bid] = {
                "barbershop_id": bid,
                "name": row["name"],
                "postcode": row["postcode"].strip(),
                "lat": row["location_lat"],
                "lng": row["location_lng"],
                "phone": row["phone"],
                "website": row["website"],
                "barbers": [],
            }
        if row["barber_id"] is not None:
            shops[bid]["barbers"].append(
                {
                    "barber_id": row["barber_id"],
                    "username": row["username"],
                    "profile_image_url": row["profile_image_url"],
                }
            )

    return list(shops.values())


def fetch_discover_search_items():
    items = [
        {"id": 0, "type": "filter", "label": "Closest"},
        {"id": 1, "type": "filter", "label": "Highest rated"},
        {"id": 2, "type": "filter", "label": "Most recent"},
    ]

    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT tag_id, name FROM Tag ORDER BY name ASC")
            for r in cur.fetchall():
                items.append({"id": int(r["tag_id"]), "type": "tag", "label": r["name"]})

            cur.execute(
                """
                SELECT b.barber_id, u.username
                FROM Barber b
                JOIN App_User u ON u.user_id = b.user_id
                ORDER BY u.username ASC
                """
            )
            for r in cur.fetchall():
                items.append(
                    {"id": int(r["barber_id"]), "type": "barber", "label": r["username"]}
                )

            cur.execute("SELECT barbershop_id, name FROM Barbershop ORDER BY name ASC")
            for r in cur.fetchall():
                items.append(
                    {"id": int(r["barbershop_id"]), "type": "barbershop", "label": r["name"]}
                )

    return items