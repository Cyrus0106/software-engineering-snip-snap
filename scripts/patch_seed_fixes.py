"""
Patch script — fixes three issues with the initial seed:
1. Set location_lat/location_lng on each seed barber's App_User row
2. Add websites to all seed barbershops
3. Add gallery photos (is_post=False, with main_tag) for each seed barber
"""
import os, random, uuid, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from dotenv import load_dotenv
import requests
from supabase import create_client

load_dotenv()

BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "haircuts")

SHOP_WEBSITES = {
    "The Fade Room":        "https://thefaderoom.co.uk",
    "Sharps Barbers":       "https://sharpsbarbers.co.uk",
    "Brum Cuts":            "https://brumcuts.co.uk",
    "Headmasters Leeds":    "https://headmastersleeds.co.uk",
    "The Barber Quarter":   "https://thebarberquarter.co.uk",
    "Bristol Blade Co.":    "https://bristolblade.co.uk",
    "Liverpool Lads":       "https://liverpoollads.co.uk",
    "Notts Cuts":           "https://nottscuts.co.uk",
    "Cardiff Classics":     "https://cardiffclassics.co.uk",
    "Newcastle Napes":      "https://newcastlenapes.co.uk",
}

# Tag IDs to use as main_tag (barber-style tags)
TAG_IDS = [1, 2, 3, 8, 9, 10, 11, 12, 14, 16, 17, 18, 19]

def get_conn():
    db_url = os.environ["DATABASE_URL"]
    if "sslmode=" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
    return psycopg2.connect(db_url)

def get_sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
_unsplash_cache: list = []

def _fetch_unsplash_pool():
    global _unsplash_cache
    for query in ["haircut", "barber fade", "mens haircut", "barbershop", "hair fade"]:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 30, "orientation": "portrait"},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=15,
        )
        if resp.ok:
            for item in resp.json().get("results", []):
                url = item["urls"].get("regular")
                w, h = item.get("width", 400), item.get("height", 600)
                if url:
                    _unsplash_cache.append((url, w, h))
    random.shuffle(_unsplash_cache)
    print(f"  Unsplash pool: {len(_unsplash_cache)} images loaded.")

def upload_image(sb, barber_id, img_index, offset=500):
    if UNSPLASH_KEY:
        if not _unsplash_cache:
            _fetch_unsplash_pool()
        url, w, h = _unsplash_cache[(barber_id * 20 + img_index + offset) % len(_unsplash_cache)]
    else:
        w, h = 400, 400
        seed = barber_id * 100 + img_index + offset
        url = f"https://picsum.photos/seed/{seed}/{w}/{h}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    path = f"barber_{barber_id}/{uuid.uuid4()}.jpg"
    try:
        sb.storage.from_(BUCKET).upload(path, resp.content, file_options={"content-type": "image/jpeg"})
    except TypeError:
        sb.storage.from_(BUCKET).upload(path, resp.content)
    return path, w, h

conn = get_conn()
sb = get_sb()
cur = conn.cursor()

# ── 1. Set lat/lng on seed barbers' App_User rows ────────────────────────────
print("1. Setting location lat/lng on seed barber accounts...")
cur.execute("""
    SELECT u.user_id, bs.location_lat, bs.location_lng
    FROM App_User u
    JOIN Barber b ON b.user_id = u.user_id
    JOIN Barbershop bs ON bs.barbershop_id = b.barbershop_id
    WHERE u.email LIKE '%@seed.snipsnap' AND u.role = 'barber'
""")
rows = cur.fetchall()
for user_id, lat, lng in rows:
    cur.execute(
        "UPDATE App_User SET location_lat = %s, location_lng = %s WHERE user_id = %s",
        (lat, lng, user_id),
    )
conn.commit()
print(f"   Updated {len(rows)} barber accounts with shop coordinates.")

# ── 2. Add websites to seed barbershops ──────────────────────────────────────
print("2. Adding websites to seed barbershops...")
updated = 0
for name, website in SHOP_WEBSITES.items():
    cur.execute(
        "UPDATE Barbershop SET website = %s WHERE name = %s AND (website IS NULL OR website = '')",
        (website, name),
    )
    updated += cur.rowcount
conn.commit()
print(f"   Updated {updated} barbershops with websites.")

# ── 3. Add gallery photos (is_post=False) for each seed barber ───────────────
print("3. Adding gallery photos for seed barbers (this may take a while)...")
cur.execute("""
    SELECT b.barber_id FROM Barber b
    JOIN App_User u ON b.user_id = u.user_id
    WHERE u.email LIKE '%@seed.snipsnap'
""")
barber_ids = [r[0] for r in cur.fetchall()]

total = 0
for idx, barber_id in enumerate(barber_ids):
    num_gallery = random.randint(4, 8)
    for j in range(num_gallery):
        try:
            path, w, h = upload_image(sb, barber_id, j)
            tag_id = random.choice(TAG_IDS)
            cur.execute(
                """
                INSERT INTO HaircutPhoto (barber_id, image_url, width_px, height_px, is_post, main_tag, status)
                VALUES (%s, %s, %s, %s, FALSE, %s, 'show')
                """,
                (barber_id, path, w, h, tag_id),
            )
            conn.commit()
            total += 1
        except Exception as e:
            conn.rollback()
            print(f"   Warning: failed for barber {barber_id} img {j}: {e}")
    print(f"   Barber {idx+1}/{len(barber_ids)}: {num_gallery} gallery photos added")

cur.close()
conn.close()
print(f"\nDone -- {total} gallery photos added across {len(barber_ids)} barbers.")
