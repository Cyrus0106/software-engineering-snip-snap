import os
import random
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv
import psycopg2
from ..db import _get_conn
load_dotenv()

MIN_PHOTOS_PER_BARBER = 20
TAG_ID_MIN = 1
TAG_ID_MAX = 20
HIDDEN_RATIO = 0.10
POST_RATIO = 0.50


# Spread timestamps over the last 180 days.
MAX_AGE_DAYS = 180


def get_storage_image_pool():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

    sb = create_client(url, key)

    res = sb.storage.from_("photos").list("haircuts")

    if not res:
        raise RuntimeError("No files found in photos/haircuts")

    paths = []
    for item in res:
        name = item.get("name")
        if not name:
            continue
        paths.append(f"haircuts/{name}")

    if not paths:
        raise RuntimeError("No usable image paths found in photos/haircuts")

    return paths


def random_timestamp() -> datetime:
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, MAX_AGE_DAYS),
        seconds=random.randint(0, 24 * 60 * 60 - 1),
    )
    return now - delta


def choose_status() -> str:
    return "hide" if random.random() < HIDDEN_RATIO else "show"


def choose_is_post() -> bool:
    return random.random() < POST_RATIO


def choose_dimensions() -> tuple[int, int]:
    # Mostly portrait/square social-style images
    options = [
        (1080, 1080),
        (1080, 1350),
        (1200, 1200),
        (1080, 1440),
        (1440, 1440),
    ]
    return random.choice(options)


def choose_tags() -> list[int]:
    # 1 to 5 tags per photo, no duplicates
    tag_count = random.randint(1, 5)
    return random.sample(range(TAG_ID_MIN, TAG_ID_MAX + 1), k=tag_count)


def main() -> None:
    conn = _get_conn()
    conn.autocommit = False


    STORAGE_IMAGE_POOL = get_storage_image_pool()
    print(f"Loaded {len(STORAGE_IMAGE_POOL)} storage images from photos/haircuts")

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT barber_id FROM barber ORDER BY barber_id ASC")
            barber_rows = cur.fetchall()

            if not barber_rows:
                raise RuntimeError("No barbers found in barber table")

            barber_ids = [row[0] for row in barber_rows]

            photo_insert_sql = """
                INSERT INTO haircutphoto (
                    barber_id,
                    image_url,
                    width_px,
                    height_px,
                    status,
                    main_tag,
                    is_post,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING photo_id
            """

            tag_insert_sql = """
                INSERT INTO haircutphoto_tag (photo_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """

            total_photos = 0
            total_tag_links = 0

            for barber_id in barber_ids:
                for _ in range(MIN_PHOTOS_PER_BARBER):
                    image_path = random.choice(STORAGE_IMAGE_POOL)
                    width_px, height_px = choose_dimensions()
                    status = choose_status()
                    is_post = choose_is_post()
                    created_at = random_timestamp()
                    tag_ids = choose_tags()
                    main_tag = random.choice(tag_ids)

                    cur.execute(
                        photo_insert_sql,
                        (
                            barber_id,
                            image_path,
                            width_px,
                            height_px,
                            status,
                            main_tag,
                            is_post,
                            created_at,
                        ),
                    )
                    photo_id = cur.fetchone()[0]
                    total_photos += 1

                    for tag_id in tag_ids:
                        cur.execute(tag_insert_sql, (photo_id, tag_id))
                        total_tag_links += 1

        conn.commit()
        print(f"Inserted {total_photos} haircutphoto rows")
        print(f"Inserted {total_tag_links} haircutphoto_tag rows")
        print(f"Barbers covered: {len(barber_ids)}")
        print(f"Photos per barber: {MIN_PHOTOS_PER_BARBER}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()