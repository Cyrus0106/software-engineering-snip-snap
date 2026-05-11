import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from dotenv import load_dotenv
load_dotenv()

REVIEW_COMMENTS = [
    "Amazing cut -- will definitely be back.",
    "Best barber I've visited in years. Highly recommend.",
    "Great atmosphere and a really clean fade.",
    "Quick service, excellent result. Couldn't be happier.",
    "Very professional, great attention to detail.",
    "Perfect trim as always -- never disappoints.",
    "Friendly staff and a top-quality haircut.",
    "Fade was absolutely on point. 10/10.",
    "Really happy with my new style.",
    "Took their time and got it exactly right.",
    "Decent cut, had to wait a bit but worth it.",
    "Good barber, consistent quality. Will return.",
    "Solid experience, very pleased.",
    "Clean shop, great vibe and an excellent cut.",
    "Honestly couldn't be happier with the result.",
    "First time here -- won't be the last.",
    "Recommended by a friend and they were right.",
    "Transformed my look. Brilliant work.",
]

BARBER_REPLIES = [
    "Thank you so much, really appreciate the kind words!",
    "Glad you enjoyed it, hope to see you again soon!",
    "Thanks for the feedback, means a lot to us.",
    "Great to hear, see you next time!",
    "Appreciate you taking the time to leave a review!",
]

CUSTOMER_REPLIES = [
    "Definitely coming back next month!",
    "Already booked my next appointment.",
    "Brought my mate along last week too, he loved it.",
    "Will be recommending to everyone I know.",
]

SHOP_COMMENTS = [
    "Brilliant barbershop, great team and lovely atmosphere.",
    "Clean shop, friendly staff, will be back.",
    "Really impressed with the whole experience.",
    "Best barbershop in the area, no question.",
    "Great prices and even better haircuts.",
    "Walked in and was seen quickly. Top place.",
]

db_url = os.environ["DATABASE_URL"]
if "sslmode=" not in db_url:
    db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("SELECT user_id FROM App_User WHERE email LIKE '%@seed.snipsnap' AND role='customer'")
customer_ids = [r[0] for r in cur.fetchall()]

cur.execute("""
    SELECT b.barber_id, b.user_id FROM Barber b
    JOIN App_User u ON b.user_id = u.user_id
    WHERE u.email LIKE '%@seed.snipsnap'
""")
barbers = cur.fetchall()  # list of (barber_id, user_id)

cur.execute("""
    SELECT bs.barbershop_id FROM Barbershop bs
    WHERE bs.name IN (
        'The Fade Room','Sharps Barbers','Brum Cuts','Headmasters Leeds',
        'The Barber Quarter','Bristol Blade Co.','Liverpool Lads',
        'Notts Cuts','Cardiff Classics','Newcastle Napes'
    )
""")
shop_ids = [r[0] for r in cur.fetchall()]

print(f"Found {len(customer_ids)} customers, {len(barbers)} barbers, {len(shop_ids)} shops")

total_reviews = 0
total_replies = 0
total_shop_reviews = 0

# Barber reviews + replies
for barber_id, barber_user_id in barbers:
    num = random.randint(5, 10)
    reviewers = random.sample(customer_ids, num)
    review_ids = []
    for cust_id in reviewers:
        rating = random.choices([3, 4, 5], weights=[1, 3, 6])[0]
        text = random.choice(REVIEW_COMMENTS)
        cur.execute(
            "INSERT INTO review (target_barber_id, user_id, text, rating, status) VALUES (%s, %s, %s, %s, 'show') RETURNING review_id",
            (barber_id, cust_id, text, rating),
        )
        review_ids.append((cur.fetchone()[0], cust_id))
        total_reviews += 1

    # A few replies: barber replies to 2 reviews, a customer replies to 1
    # Replies must still set target_barber_id due to DB check constraint
    for review_id, cust_id in random.sample(review_ids, min(2, len(review_ids))):
        cur.execute(
            "INSERT INTO review (parent_review_id, target_barber_id, user_id, text, status) VALUES (%s, %s, %s, %s, 'show')",
            (review_id, barber_id, barber_user_id, random.choice(BARBER_REPLIES)),
        )
        total_replies += 1

    if review_ids:
        review_id, orig_cust_id = random.choice(review_ids)
        other_customers = [c for c in customer_ids if c != orig_cust_id]
        replying_cust = random.choice(other_customers)
        cur.execute(
            "INSERT INTO review (parent_review_id, target_barber_id, user_id, text, status) VALUES (%s, %s, %s, %s, 'show')",
            (review_id, barber_id, replying_cust, random.choice(CUSTOMER_REPLIES)),
        )
        total_replies += 1

# Barbershop reviews (3–4 per shop)
for shop_id in shop_ids:
    for cust_id in random.sample(customer_ids, random.randint(3, 4)):
        rating = random.choices([3, 4, 5], weights=[1, 3, 6])[0]
        cur.execute(
            "INSERT INTO review (target_barbershop_id, user_id, text, rating, status) VALUES (%s, %s, %s, %s, 'show')",
            (shop_id, cust_id, random.choice(SHOP_COMMENTS), rating),
        )
        total_shop_reviews += 1

conn.commit()
cur.close()
conn.close()
print(f"Done -- {total_reviews} barber reviews, {total_replies} replies, {total_shop_reviews} shop reviews inserted.")
