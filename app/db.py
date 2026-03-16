import os
import psycopg2
import psycopg2.extras
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def _get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    # Supabase Postgres requires SSL. Enforce if not present in the URL.
    if "sslmode=" not in db_url:
        sep = "&" if "?" in db_url else "?"

    return psycopg2.connect(db_url)


def link_auth_user_id(email: str, auth_user_id: str) -> None:
    """
    Link Supabase auth user UUID to App_User row (only if not already linked).
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE App_User
                SET auth_user_id = %s
                WHERE email = %s
                  AND auth_user_id IS NULL
                """,
                (auth_user_id, email),
            )
        conn.commit()

def get_app_user_by_auth_user_id(auth_user_id: str):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, auth_user_id, email, username, role
                FROM App_User
                WHERE auth_user_id = %s
                """,
                (auth_user_id,),
            )
            row = cur.fetchone()

    if not row:
        return None

    return {
        "user_id": row[0],
        "auth_user_id": row[1],
        "email": row[2],
        "username": row[3],
        "role": row[4],
    }

def get_app_user_by_email(email: str):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, auth_user_id, email, username, role
                FROM App_User
                WHERE email = %s
                """,
                (email,),
            )
            row = cur.fetchone()

    if not row:
        return None

    return {
        "user_id": row[0],
        "auth_user_id": row[1],
        "email": row[2],
        "username": row[3],
        "role": row[4],
    }

def get_user_promo(user_id: int):
    """Get user profile data for the userPromo component."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
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

    raw_url = row[2]
    image_url = None
    if raw_url and "/profiles/" in raw_url:
        image_url = raw_url.replace("/static/uploads/profiles/", "/static/uploads/profile_photos/")
    elif raw_url:
        image_url = raw_url

    return {
        "name": row[0] or "Unknown",
        "role": row[1] or "",
        "profile_image_url": image_url,
        "barbershop_name": row[3] or "",
    }


def get_barber_public_by_user_id(user_id: int):
    """
    Public barber profile (safe fields only).
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, username, location_lat, location_lng, postcode, role
                FROM App_User
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()

    if not row:
        return None

    role = (row[5] or "").strip().lower()
    if role != "barber":
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "location_lat": row[2],
        "location_lng": row[3],
        "postcode": row[4],
        "role": role,
    }


def update_barber_profile(user_id: int, username: str | None, postcode: str | None, lat, lng) -> None:
    """
    Barber edits their own public profile.
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE App_User
                SET
                  username = COALESCE(%s, username),
                  postcode = COALESCE(%s, postcode),
                  location_lat = %s,
                  location_lng = %s
                WHERE user_id = %s
                """,
                (username, postcode, lat, lng, user_id),
            )
        conn.commit()


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

# fetch_discover_posts is a complex query builder for the discover page, supporting multiple optional filters and sorts, and calculating distance and blended scores for ranking.
# It returns a list of haircut posts with associated promo info, ratings, and distance if viewer location is provided.
# It is a very important function for the discover page performance and relevance, and is carefully optimized with conditional joins and where clauses based on the provided filters.
def fetch_discover_posts(
    tag_ids: List[int],
    barber_ids: List[int],
    barbershop_ids: List[int],
    cursor: Optional[Tuple[datetime, int]],
    limit: int,
    effective_sort: str,
    viewer_lat: float | None = None,
    viewer_lng: float | None = None,
) -> List[Dict[str, Any]]:
    where: List[str] = ["hp.is_post = TRUE", "hp.status = 'show'"]
    where_params: List[Any] = []
    select_params: List[Any] = []
    join: List[str] = []
    having: List[str] = []

    # --- Core joins for promo + barbershop coords
    join.append("JOIN barber b_promo ON b_promo.barber_id = hp.barber_id")
    join.append("JOIN app_user u_promo ON u_promo.user_id = b_promo.user_id")
    join.append("LEFT JOIN barbershop bs_promo ON bs_promo.barbershop_id = b_promo.barbershop_id")
    join.append("LEFT JOIN profilephoto pp_promo ON pp_promo.user_id = u_promo.user_id")

    # --- Rating aggregate
    join.append("""
        LEFT JOIN (
            SELECT
                r.target_barber_id AS barber_id,
                AVG(r.rating)::float AS avg_rating,
                COUNT(*)::int AS rating_count
            FROM review r
            WHERE r.status = 'show'
              AND r.rating IS NOT NULL
              AND r.target_barber_id IS NOT NULL
            GROUP BY r.target_barber_id
        ) rating_agg ON rating_agg.barber_id = hp.barber_id
    """)

    # --- Filters
    if barbershop_ids:
        where.append("b_promo.barbershop_id = ANY(%s)")
        where_params.append(barbershop_ids)

    if barber_ids:
        where.append("hp.barber_id = ANY(%s)")
        where_params.append(barber_ids)

    if tag_ids:
        join.append("JOIN haircutphoto_tag hpt ON hpt.photo_id = hp.photo_id")
        where.append("hpt.tag_id = ANY(%s)")
        where_params.append(tag_ids)
        having.append("COUNT(DISTINCT hpt.tag_id) = %s")
        where_params.append(len(tag_ids))

    if cursor is not None:
        cursor_created_at, cursor_photo_id = cursor
        where.append("(hp.created_at < %s OR (hp.created_at = %s AND hp.photo_id < %s))")
        where_params.extend([cursor_created_at, cursor_created_at, cursor_photo_id])

    # --- Distance
    include_distance = (viewer_lat is not None and viewer_lng is not None)

    distance_expr = "NULL::float"
    distance_score_expr = "0.0::float"

    if include_distance:
        distance_expr = """
        (ST_DistanceSphere(
            ST_MakePoint(bs_promo.location_lng, bs_promo.location_lat),
            ST_MakePoint(%s, %s)
        ) / 1000.0)::float
        """
        # SELECT placeholders come before WHERE placeholders
        select_params.extend([viewer_lng, viewer_lat])

        distance_score_expr = """
        (1.0 / (1.0 + (
            ST_DistanceSphere(
                ST_MakePoint(bs_promo.location_lng, bs_promo.location_lat),
                ST_MakePoint(%s, %s)
            ) / 1000.0
        )))
        """
        # blended_score uses distance again, so add them again
        select_params.extend([viewer_lng, viewer_lat])

    # --- Scoring
    rating_score_expr = "COALESCE(rating_agg.avg_rating, 0)::float / 5.0"
    recency_score_expr = """
    (1.0 / (1.0 + (EXTRACT(EPOCH FROM (NOW() - hp.created_at)) / 86400.0)))
    """

    blended_score_expr = f"""
    (
        0.45 * ({distance_score_expr}) +
        0.35 * ({rating_score_expr}) +
        0.20 * ({recency_score_expr})
    )::float
    """

    # --- Ordering
    if effective_sort == "closest" and include_distance:
        order_by = "distance_km ASC, hp.created_at DESC, hp.photo_id DESC"
    elif effective_sort == "highest_rated":
        order_by = "rating_agg.avg_rating DESC NULLS LAST, rating_agg.rating_count DESC, hp.created_at DESC, hp.photo_id DESC"
    elif effective_sort == "blended":
        order_by = "blended_score DESC, hp.created_at DESC, hp.photo_id DESC"
    else:
        order_by = "hp.created_at DESC, hp.photo_id DESC"

    having_sql = f"HAVING {' AND '.join(having)}" if having else ""

    sql = f"""
        SELECT
            hp.photo_id,
            hp.image_url,
            hp.width_px,
            hp.height_px,
            hp.created_at,
            hp.barber_id,

            u_promo.username AS promo_name,
            u_promo.role AS promo_role,
            bs_promo.name AS promo_barbershop_name,
            pp_promo.image_url AS promo_profile_image_url,

            bs_promo.location_lat AS shop_lat,
            bs_promo.location_lng AS shop_lng,

            rating_agg.avg_rating AS avg_rating,
            rating_agg.rating_count AS rating_count,

            {distance_expr} AS distance_km,
            {blended_score_expr} AS blended_score

        FROM haircutphoto hp
        {' '.join(join)}
        WHERE {' AND '.join(where)}
        GROUP BY
            hp.photo_id, hp.image_url, hp.width_px, hp.height_px, hp.created_at, hp.barber_id,
            u_promo.username, u_promo.role, bs_promo.name, pp_promo.image_url,
            bs_promo.location_lat, bs_promo.location_lng,
            rating_agg.avg_rating, rating_agg.rating_count
        {having_sql}
        ORDER BY {order_by}
        LIMIT %s
    """

    params = select_params + where_params + [limit]

    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return rows

def get_user_location(user_id: int):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT location_lat, location_lng FROM App_User WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
    if not row:
        return None
    lat, lng = row
    if lat is None or lng is None:
        return None
    return {"lat": float(lat), "lng": float(lng)}

def _pick_label(row: Dict[str, Any], preferred_keys: List[str]) -> str:
    for k in preferred_keys:
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for k, v in row.items():
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""



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