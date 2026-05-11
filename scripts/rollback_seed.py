"""
Rollback script -- removes all data inserted by the seed scripts.
Deletes in reverse dependency order to avoid FK constraint errors.
Run from project root: python scripts/rollback_seed.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SEED_SUFFIX = "@seed.snipsnap"
SEED_SHOP_NAMES = [
    "The Fade Room", "Sharps Barbers", "Brum Cuts", "Headmasters Leeds",
    "The Barber Quarter", "Bristol Blade Co.", "Liverpool Lads",
    "Notts Cuts", "Cardiff Classics", "Newcastle Napes",
]
BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "haircuts")

def get_conn():
    db_url = os.environ["DATABASE_URL"]
    if "sslmode=" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
    return psycopg2.connect(db_url)

conn = get_conn()
cur = conn.cursor()

# Get seed barber_ids and their storage paths before deleting anything
cur.execute("""
    SELECT b.barber_id FROM Barber b
    JOIN App_User u ON b.user_id = u.user_id
    WHERE u.email LIKE %s
""", (f"%{SEED_SUFFIX}",))
barber_ids = [r[0] for r in cur.fetchall()]
print(f"Found {len(barber_ids)} seed barbers to remove.")

# Collect storage paths for deletion
storage_paths = []
if barber_ids:
    cur.execute(
        "SELECT image_url FROM HaircutPhoto WHERE barber_id = ANY(%s)",
        (barber_ids,)
    )
    storage_paths = [r[0] for r in cur.fetchall() if r[0]]
print(f"Found {len(storage_paths)} photos to remove from storage.")

# Get seed user_ids (barbers + customers)
cur.execute("SELECT user_id FROM App_User WHERE email LIKE %s", (f"%{SEED_SUFFIX}",))
user_ids = [r[0] for r in cur.fetchall()]

# ── Delete in dependency order ────────────────────────────────────────────────

print("Deleting reviews written by or targeting seed users/barbers...")
if barber_ids:
    cur.execute("DELETE FROM review WHERE target_barber_id = ANY(%s)", (barber_ids,))
    print(f"  Barber reviews: {cur.rowcount}")
cur.execute("""
    DELETE FROM review WHERE target_barbershop_id IN (
        SELECT barbershop_id FROM Barbershop WHERE name = ANY(%s)
    )
""", (SEED_SHOP_NAMES,))
print(f"  Shop reviews: {cur.rowcount}")
if user_ids:
    cur.execute("DELETE FROM review WHERE user_id = ANY(%s)", (user_ids,))
    print(f"  Reviews by seed users: {cur.rowcount}")

print("Deleting haircut photos...")
if barber_ids:
    cur.execute("DELETE FROM HaircutPhoto WHERE barber_id = ANY(%s)", (barber_ids,))
    print(f"  {cur.rowcount} photos deleted from DB.")

print("Deleting shifts...")
if barber_ids:
    cur.execute("DELETE FROM Shift WHERE barber_id = ANY(%s)", (barber_ids,))
    print(f"  {cur.rowcount} shifts deleted.")

print("Deleting barber records...")
if barber_ids:
    cur.execute("DELETE FROM Barber WHERE barber_id = ANY(%s)", (barber_ids,))
    print(f"  {cur.rowcount} barber records deleted.")

print("Deleting App_User records...")
if user_ids:
    cur.execute("DELETE FROM App_User WHERE user_id = ANY(%s)", (user_ids,))
    print(f"  {cur.rowcount} users deleted.")

print("Deleting barbershops...")
cur.execute("DELETE FROM Barbershop WHERE name = ANY(%s)", (SEED_SHOP_NAMES,))
print(f"  {cur.rowcount} barbershops deleted.")

conn.commit()
cur.close()
conn.close()

# ── Delete storage files ──────────────────────────────────────────────────────
if storage_paths:
    print("Deleting images from Supabase storage...")
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    try:
        sb.storage.from_(BUCKET).remove(storage_paths)
        print(f"  {len(storage_paths)} files removed from storage.")
    except Exception as e:
        print(f"  Warning: storage deletion failed: {e}")
        print("  You may need to manually clear the barber_* folders in the haircuts bucket.")

print("\nRollback complete.")
