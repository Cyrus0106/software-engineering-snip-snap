#!/usr/bin/env python3
"""
Seed script: populates the database with realistic UK test data.

Run from the project root:
    python scripts/seed_data.py

Requires DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY in .env
Uploads real images to Supabase storage so posts display correctly.
Safe to inspect/revert: all seed records have emails ending in @seed.snipsnap
"""

import os
import random
import uuid
import json
import sys
import argparse

import psycopg2
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "haircuts")
SEED_EMAIL_SUFFIX = "@seed.snipsnap"


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_conn():
    db_url = os.environ["DATABASE_URL"]
    if "sslmode=" not in db_url:
        sep = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{sep}sslmode=require"
    return psycopg2.connect(db_url)


def get_sb():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )


def upload_image(sb, barber_id: int, img_index: int):
    """Download a seeded image from picsum and upload to Supabase storage."""
    w, h = 400, 600
    seed = barber_id * 100 + img_index
    resp = requests.get(f"https://picsum.photos/seed/{seed}/{w}/{h}", timeout=20)
    resp.raise_for_status()
    path = f"barber_{barber_id}/{uuid.uuid4()}.jpg"
    try:
        sb.storage.from_(BUCKET).upload(
            path, resp.content, file_options={"content-type": "image/jpeg"}
        )
    except TypeError:
        sb.storage.from_(BUCKET).upload(path, resp.content)
    return path, w, h


# ── Static data ───────────────────────────────────────────────────────────────

# 10 real UK barbershops across different cities
BARBERSHOPS = [
    ("The Fade Room",        "E1 6RF",   51.5155, -0.0613,  "https://thefaderoom.co.uk"),
    ("Sharps Barbers",       "M4 1HN",   53.4839, -2.2374,  None),
    ("Brum Cuts",            "B2 4QA",   52.4796, -1.8965,  None),
    ("Headmasters Leeds",    "LS1 2TH",  53.7987, -1.5441,  None),
    ("The Barber Quarter",   "G1 1DX",   55.8609, -4.2514,  None),
    ("Bristol Blade Co.",    "BS1 5TH",  51.4545, -2.5967,  None),
    ("Liverpool Lads",       "L1 1JF",   53.4084, -2.9916,  None),
    ("Notts Cuts",           "NG1 2FQ",  52.9548, -1.1581,  None),
    ("Cardiff Classics",     "CF10 1EP", 51.4816, -3.1791,  None),
    ("Newcastle Napes",      "NE1 6UF",  54.9783, -1.6178,  None),
]

# 30 realistic barber usernames (3 per shop)
BARBER_NAMES = [
    # Shop 1 – East London
    "jay_fades", "marcus_blade", "dan_cuts",
    # Shop 2 – Manchester
    "riley_trim", "callum_barber", "jake_sharp",
    # Shop 3 – Birmingham
    "leon_style", "ash_fade", "tyler_clips",
    # Shop 4 – Leeds
    "sam_barber", "alex_trim", "finn_style",
    # Shop 5 – Glasgow
    "rob_fade", "craig_cuts", "sean_blade",
    # Shop 6 – Bristol
    "tom_barber", "harry_fade", "ben_trim",
    # Shop 7 – Liverpool
    "liam_cuts", "owen_style", "kieran_fade",
    # Shop 8 – Nottingham
    "adam_barber", "joe_blade", "ryan_trim",
    # Shop 9 – Cardiff
    "rhys_fade", "gethin_cuts", "Ioan_style",
    # Shop 10 – Newcastle
    "matty_barber", "kev_trim", "stevie_fade",
]

BIOS = [
    "Specialist in fades and tapers with 5 years experience.",
    "Clean lines and sharp fades. Walk-ins welcome.",
    "Expert in modern and classic styles.",
    "Precision cutting — your look, perfected.",
    "Beard and hair specialist. Award-winning cuts.",
    "Creative styles for the modern man.",
    "Classic barbering with a contemporary twist.",
    "10 years behind the chair. Quality every time.",
    "Skin fades and skin care specialist.",
    "I let your hair tell your story.",
]

REVIEW_COMMENTS = [
    "Amazing cut — will definitely be back.",
    "Best barber I've visited in years. Highly recommend.",
    "Great atmosphere and a really clean fade.",
    "Quick service, excellent result. Couldn't be happier.",
    "Very professional, great attention to detail.",
    "Perfect trim as always — never disappoints.",
    "Friendly staff and a top-quality haircut.",
    "Fade was absolutely on point. 10/10.",
    "Really happy with my new style.",
    "Took their time and got it exactly right.",
    "Decent cut, had to wait a bit but worth it.",
    "Good barber, consistent quality. Will return.",
    "Solid experience, very pleased.",
    "Clean shop, great vibe and an excellent cut.",
    "Honestly couldn't be happier with the result.",
    "First time here — won't be the last.",
    "Recommended by a friend and they were right.",
    "Transformed my look. Brilliant work.",
]

DAYS = list(range(7))  # 0 = Monday … 6 = Sunday


# ── Main ──────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False):
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"=== Seed script [{mode}] ===")
    if dry_run:
        print("No data will be written. DB transaction will be rolled back at the end.\n")

    conn = get_conn()
    sb = None if dry_run else get_sb()
    cur = conn.cursor()

    # Guard: skip if seed data already exists (only in live mode)
    if not dry_run:
        cur.execute(
            "SELECT COUNT(*) FROM App_User WHERE email LIKE %s",
            (f"%{SEED_EMAIL_SUFFIX}",),
        )
        if cur.fetchone()[0] > 0:
            print("Seed data already present — aborting to avoid duplicates.")
            print("Delete rows with emails ending in @seed.snipsnap first to re-seed.")
            cur.close()
            conn.close()
            return

    # 1. Customer accounts
    print("--- 40 customer accounts ---")
    customer_ids = []
    for i in range(1, 41):
        email = f"seed_customer{i}{SEED_EMAIL_SUFFIX}"
        username = f"customer_{i}"
        if dry_run:
            print(f"  INSERT App_User  email={email}  username={username}  role=customer")
            customer_ids.append(9000 + i)  # fake id for dry run
        else:
            cur.execute(
                "INSERT INTO App_User (email, username, role) VALUES (%s, %s, 'customer') RETURNING user_id",
                (email, username),
            )
            customer_ids.append(cur.fetchone()[0])
    if not dry_run:
        conn.commit()
    print(f"  ->{len(customer_ids)} customers")

    # 2. Barbershops
    print("\n--- 10 barbershops ---")
    shop_ids = []
    for idx, (name, postcode, lat, lng, website) in enumerate(BARBERSHOPS):
        if dry_run:
            print(f"  INSERT Barbershop  name='{name}'  postcode={postcode}  lat={lat}  lng={lng}  website={website}")
            shop_ids.append(8000 + idx)
        else:
            cur.execute(
                """
                INSERT INTO Barbershop (name, postcode, location_lat, location_lng, website)
                VALUES (%s, %s, %s, %s, %s) RETURNING barbershop_id
                """,
                (name, postcode, lat, lng, website),
            )
            shop_ids.append(cur.fetchone()[0])
    if not dry_run:
        conn.commit()
    print(f"  ->{len(shop_ids)} barbershops")

    # 3. Barbers
    print("\n--- 30 barbers + shifts ---")
    barbers = []
    for i, name in enumerate(BARBER_NAMES):
        shop_id = shop_ids[i // 3]
        shop_name = BARBERSHOPS[i // 3][0]
        bio = BIOS[i % len(BIOS)]
        email = f"seed_{name}{SEED_EMAIL_SUFFIX}"
        working_days = random.sample(DAYS, random.randint(3, 5))
        shifts_preview = [f"{d}({random.randint(8,11):02d}:00-{random.randint(16,19):02d}:00)" for d in working_days]

        if dry_run:
            print(f"  INSERT Barber  username={name}  shop='{shop_name}'  shifts={shifts_preview}")
            barbers.append((7000 + i, 6000 + i, i // 3))
        else:
            cur.execute(
                "INSERT INTO App_User (email, username, role) VALUES (%s, %s, 'barber') RETURNING user_id",
                (email, name),
            )
            user_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO Barber (user_id, barbershop_id, bio) VALUES (%s, %s, %s) RETURNING barber_id",
                (user_id, shop_id, bio),
            )
            barber_id = cur.fetchone()[0]
            barbers.append((user_id, barber_id, i // 3))
            for day in working_days:
                start_h = random.randint(8, 11)
                end_h = random.randint(16, 19)
                cur.execute(
                    "INSERT INTO Shift (barber_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s)",
                    (barber_id, day, f"{start_h:02d}:00", f"{end_h:02d}:00"),
                )
    if not dry_run:
        conn.commit()
    print(f"  ->{len(barbers)} barbers with shifts")

    # 4. Haircut posts
    print("\n--- Haircut posts (5–10 per barber) ---")
    total_posts = 0
    for idx, (user_id, barber_id, _) in enumerate(barbers):
        num_posts = random.randint(5, 10)
        total_posts += num_posts
        if dry_run:
            print(f"  Barber {idx+1} ({BARBER_NAMES[idx]}): {num_posts} posts — images would be uploaded to storage")
        else:
            for j in range(num_posts):
                try:
                    path, w, h = upload_image(sb, barber_id, j)
                    cur.execute(
                        "INSERT INTO HaircutPhoto (barber_id, image_url, width_px, height_px, is_post) VALUES (%s, %s, %s, %s, TRUE)",
                        (barber_id, path, w, h),
                    )
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print(f"  Warning: upload failed barber {barber_id} img {j}: {e}")
            print(f"  Barber {idx+1}/{len(barbers)} done ({num_posts} posts)")
    print(f"  ->~{total_posts} total posts")

    # 5. Reviews
    print("\n--- Reviews (5–10 per barber) ---")
    total_reviews = 0
    for user_id, barber_id, shop_idx in barbers:
        num_reviews = random.randint(5, 10)
        total_reviews += num_reviews
        reviewers = random.sample(customer_ids, num_reviews)
        if dry_run:
            ratings = [random.choices([3, 4, 5], weights=[1, 3, 6])[0] for _ in reviewers]
            print(f"  Barber {barber_id}: {num_reviews} reviews  ratings={ratings}")
        else:
            for cust_id in reviewers:
                rating = random.choices([3, 4, 5], weights=[1, 3, 6])[0]
                comment = random.choice(REVIEW_COMMENTS)
                cur.execute(
                    "INSERT INTO review (barber_profile_id, customer_user_id, rating, comment) VALUES (%s, %s, %s, %s)",
                    (barber_id, cust_id, rating, comment),
                )
            conn.commit()
    print(f"  ->~{total_reviews} total reviews")

    # Finish
    if dry_run:
        conn.rollback()
        print("\n=== DRY RUN complete — nothing was written to the database. ===")
    else:
        cur.close()
        conn.close()
        print("\n=== Seed complete! All data inserted successfully. ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Snip-Snap database with test data.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be inserted without writing anything.")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
