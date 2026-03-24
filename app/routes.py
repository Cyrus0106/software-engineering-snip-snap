import os
from flask import render_template, request, redirect, session, url_for, jsonify, abort
from .auth import verify_supabase_jwt
from .input_sanitization import sanitize_input
from .access import login_required, roles_required
from .db import get_user_location, link_auth_user_id, get_app_user_by_auth_user_id, get_app_user_by_email, get_user_promo, get_barber_public_by_user_id, update_barber_profile, get_barbershop_by_id, get_shifts_for_barber, get_shop_opening_hours, get_all_barbershops, get_barber_shop_id, update_barber_shop, create_barbershop, upsert_profile_photo
from .supabase_storage import upload_profile_photo
from uuid import uuid4
from datetime import datetime, time
import requests as http_requests

def get_closing_soon_info(close_time_str, current_day_num):
    """
    Check if a closing time is within the next 2 hours.
    Returns dict with 'closing_soon' bool and 'mins_until_close' int.
    """
    try:
        now = datetime.now()
        current_mins = now.hour * 60 + now.minute
        
        # Parse close time (format: "HH:MM")
        close_parts = close_time_str.split(':')
        close_hour = int(close_parts[0])
        close_min = int(close_parts[1])
        close_mins = close_hour * 60 + close_min
        
        # Calculate minutes until close (same day)
        mins_until_close = close_mins - current_mins
        
        # If negative, shop has already closed or closing is tomorrow
        if mins_until_close < 0:
            return {"closing_soon": False, "mins_until_close": 0}
        
        # Check if closing within next 2 hours (120 minutes)
        if mins_until_close <= 120:
            return {"closing_soon": True, "mins_until_close": mins_until_close}
        
        return {"closing_soon": False, "mins_until_close": 0}
    except:
        return {"closing_soon": False, "mins_until_close": 0}

def geocode_postcode(postcode: str):
    """Returns (lat, lng) for a UK postcode, or (None, None) if not found."""
    try:
        r = http_requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": postcode, "format": "json", "limit": 1, "countrycodes": "gb"},
            headers={"User-Agent": "SnipSnap/1.0"},
            timeout=5,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None


def get_current_day_num():
    """Get current day of week (0=Monday, 6=Sunday)."""
    return datetime.now().weekday()

def register_routes(app):

    print("SUPABASE_URL =", os.getenv("SUPABASE_URL"))

    @app.route("/")
    def home():
        return render_template("pages/welcome.html")

    @app.route("/login")
    def login():
        return render_template(
            "pages/login.html",
            supabase_url=os.environ["SUPABASE_URL"],
            supabase_anon_key=os.environ["SUPABASE_ANON_KEY"],
        )

    @app.route("/signup")
    def signup():
        return render_template(
            "pages/signup.html",
            supabase_url=os.environ["SUPABASE_URL"],
            supabase_anon_key=os.environ["SUPABASE_ANON_KEY"],
        )

    @app.route("/logout")
    def logout():
        session.pop("user", None)
        return redirect(url_for("home"))

    # OAuth redirect lands here (browser page that will POST token to /auth/callback)
    @app.route("/auth/redirect")
    def auth_redirect():
        return render_template(
            "pages/auth_redirect.html",
            supabase_url=os.environ["SUPABASE_URL"],
            supabase_anon_key=os.environ["SUPABASE_ANON_KEY"],
        )

    @app.post("/auth/callback")
    def auth_callback():
        print("\n--- AUTH CALLBACK START ---")

        data = request.get_json(silent=True) or {}
        print("Received JSON:", data)

        access_token = data.get("access_token")
        if not access_token:
            print("No access_token received")
            return jsonify({"ok": False, "error": "Missing access_token"}), 400

        print("Access token received. Verifying...")

        try:
            claims = verify_supabase_jwt(access_token)
            print("JWT verified. Claims:", claims)
        except Exception as e:
            print("JWT verification failed:", repr(e))
            return jsonify({"ok": False, "error": str(e)}), 401

        auth_user_id = claims.get("sub")
        email = claims.get("email")

        print("JWT sub:", auth_user_id)
        print("JWT email:", email)

        from .db import get_app_user_by_auth_user_id, link_auth_user_id, get_app_user_by_email

        # Try to get user by auth_user_id first
        app_user = get_app_user_by_auth_user_id(auth_user_id)
        print("DB lookup by auth_user_id:", app_user)

        # If not found, try to link by email
        if not app_user:
            print("Not found by auth_user_id, attempting to link by email...")
            try:
                linked = link_auth_user_id(email, auth_user_id)
                print(f"Link result: {linked}")
                
                # Try lookup again
                app_user = get_app_user_by_auth_user_id(auth_user_id)
                print("DB lookup after linking:", app_user)
            except Exception as e:
                print(f"Failed to link auth_user_id: {e}")

        # Final fallback: lookup by email only
        if not app_user:
            print("Not found by auth_user_id, trying lookup by email...")
            try:
                app_user = get_app_user_by_email(email)
                print("DB lookup by email:", app_user)
            except Exception as e:
                print(f"Failed lookup by email: {e}")

        if not app_user:
            print("No App_User found for auth_user_id or email")
            return jsonify({"ok": False, "error": "User not found in App_User"}), 403

        session["user"] = {
            "id": app_user["user_id"],
            "auth_user_id": app_user["auth_user_id"],
            "email": app_user["email"],
            "username": app_user["username"],
            "role": (app_user["role"] or "").strip().lower(),
        }

        print("Session set to:", session["user"])
        print("--- AUTH CALLBACK END ---\n")

        return jsonify({"ok": True})
    
    
    @app.post("/guest/start")
    def guest_start():
        session["user"] = {
            "id": None,
            "auth_user_id": None,
            "email": None,
            "username": f"guest-{uuid4().hex[:8]}",
            "role": "guest",
            "guest_started_at": datetime.utcnow().isoformat() + "Z",
        }
        return redirect(url_for("discover"))
    

    @app.get("/whoami")
    def whoami():
        print("Current session:", session.get("user"))
        return jsonify(session.get("user") or {})
    
    @app.get("/discover")
    @login_required
    def discover():
        user = session["user"]
        viewer_loc = None

        # Only customers get distance; guests/barbers won’t show it unless you want them to.
        u = session.get("user") or {}
        uid = u.get("id")
        viewer_loc = get_user_location(int(uid)) if uid else None

        return render_template("pages/discover.html", viewer_loc=viewer_loc)
    
    @app.route("/map")
    @login_required
    def map_page():
        u = session.get("user") or {}
        uid = u.get("id")
        loc = get_user_location(int(uid)) if uid else None
        return render_template("pages/map.html", user_location=loc)


    @app.route("/profile")
    @roles_required("customer", "barber")   # guests cannot access
    def profile():
        return render_template("pages/profile.html")
    

    @app.get("/barber")
    def barber_profile():
        """
        Public route.
        If ?barber_id= is missing, show lookup form.
        If present, show that barber profile.
        """
        barber_id = request.args.get("barber_id", "").strip()

        if not barber_id:
            return render_template("pages/barber_profile.html", barber=None, barber_id=None)

        if not barber_id.isdigit():
            return render_template(
                "pages/barber_profile.html",
                barber=None,
                barber_id=barber_id,
                error="Barber id must be a number.",
            )

        barber = get_barber_public_by_user_id(int(barber_id))
        if not barber:
            return render_template(
                "pages/barber_profile.html",
                barber=None,
                barber_id=barber_id,
                error="No barber found with that id.",
            )

        barber_promo = get_user_promo(int(barber_id))
        shifts = get_shifts_for_barber(int(barber_id))
        current_day = get_current_day_num()
        
        # Calculate closing soon info for today's shifts
        closing_info = {}
        if current_day in shifts and shifts[current_day]:
            # Get the last shift for today
            last_shift = shifts[current_day][-1]
            closing_info = get_closing_soon_info(last_shift["end_time"], current_day)
        
        return render_template(
            "pages/barber_profile.html", 
            barber=barber, 
            barber_promo=barber_promo, 
            shifts=shifts, 
            barber_id=barber_id,
            current_day=current_day,
            closing_info=closing_info
        )


    @app.get("/barber/<int:barber_id>")
    def barber_profile_by_id(barber_id: int):
        """
        Convenience route: /barber/123
        """
        return redirect(url_for("barber_profile", barber_id=barber_id))


    @app.get("/barbershop/<int:barbershop_id>")
    def barbershop_profile(barbershop_id: int):
        """
        Public barbershop profile showing all barbers at this shop.
        """
        shop = get_barbershop_by_id(barbershop_id)
        if not shop:
            return render_template(
                "pages/barbershop_profile.html",
                shop=None,
                error="Barbershop not found."
            )

        opening_hours = get_shop_opening_hours(barbershop_id)
        current_day = get_current_day_num()
        
        # Calculate closing soon info for today
        closing_info = {}
        if current_day in opening_hours:
            closing_info = get_closing_soon_info(opening_hours[current_day]["close"], current_day)
        
        return render_template(
            "pages/barbershop_profile.html", 
            shop=shop, 
            opening_hours=opening_hours,
            current_day=current_day,
            closing_info=closing_info
        )
    

    @app.route("/dashboard", methods=["GET", "POST"])
    @roles_required("barber")
    def dashboard():
        user = session["user"]
        user_id = int(user["id"])

        if request.method == "POST":
            username = (request.form.get("username") or "").strip() or None
            postcode = (request.form.get("postcode") or "").strip() or None

            if username and len(username) > 50:
                username = username[:50]
            if postcode and len(postcode) > 10:
                return render_template("pages/dashboard.html", error="Postcode too long.")
            if username:
                err = sanitize_input(username)
                if err:
                    return render_template("pages/dashboard.html", error=err)

            # Geocode postcode to lat/lng
            lat, lng = None, None
            if postcode:
                lat, lng = geocode_postcode(postcode)

            update_barber_profile(user_id=user_id, username=username, postcode=postcode, lat=lat, lng=lng)

            # Handle barbershop update
            barbershop_action = request.form.get("barbershop_action", "existing")
            if barbershop_action == "new":
                new_shop_name = (request.form.get("new_shop_name") or "").strip()
                new_shop_postcode = (request.form.get("new_shop_postcode") or "").strip()
                if new_shop_name:
                    shop_id = create_barbershop(new_shop_name, new_shop_postcode)
                    update_barber_shop(user_id, shop_id)
            else:
                barbershop_id_raw = (request.form.get("barbershop_id") or "").strip()
                if barbershop_id_raw.isdigit():
                    update_barber_shop(user_id, int(barbershop_id_raw))

            # Handle profile picture upload
            photo_file = request.files.get("profile_picture")
            if photo_file and photo_file.filename:
                allowed_types = {"image/jpeg", "image/png", "image/webp"}
                if photo_file.content_type in allowed_types:
                    file_bytes = photo_file.read()
                    if len(file_bytes) <= 5 * 1024 * 1024:
                        try:
                            path = upload_profile_photo(user_id, file_bytes, photo_file.content_type)
                            upsert_profile_photo(user_id, path)
                        except Exception as e:
                            print(f"Profile photo upload failed: {e}")

            return redirect(url_for("dashboard"))

        barber = get_barber_public_by_user_id(user_id)
        all_shops = get_all_barbershops()
        current_shop_id = get_barber_shop_id(user_id)
        promo = get_user_promo(user_id)
        return render_template("pages/dashboard.html", barber=barber, all_shops=all_shops, current_shop_id=current_shop_id, promo=promo)