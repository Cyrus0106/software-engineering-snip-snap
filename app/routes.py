import os
from flask import render_template, request, redirect, session, url_for, jsonify, abort
from .auth import verify_supabase_jwt
from .access import login_required, roles_required
from .db import get_user_location, link_auth_user_id, get_app_user_by_auth_user_id, get_app_user_by_email, get_user_promo, get_barber_public_by_user_id, update_barber_profile
from uuid import uuid4
from datetime import datetime

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

        from .db import get_app_user_by_auth_user_id

        app_user = get_app_user_by_auth_user_id(auth_user_id)
        print("DB lookup result:", app_user)

        if not app_user:
            print("No App_User found for auth_user_id")
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
        return render_template("pages/map.html")


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

        return render_template("pages/barber_profile.html", barber=barber, barber_id=barber_id)


    @app.get("/barber/<int:barber_id>")
    def barber_profile_by_id(barber_id: int):
        """
        Convenience route: /barber/123
        """
        return redirect(url_for("barber_profile", barber_id=barber_id))
    

    @app.route("/dashboard", methods=["GET", "POST"])
    @roles_required("barber")
    def dashboard():
        user = session["user"]
        user_id = int(user["id"])

        if request.method == "POST":
            username = (request.form.get("username") or "").strip() or None
            postcode = (request.form.get("postcode") or "").strip() or None

            # Allow blanks to mean NULL
            lat_raw = (request.form.get("location_lat") or "").strip()
            lng_raw = (request.form.get("location_lng") or "").strip()

            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None

            update_barber_profile(user_id=user_id, username=username, postcode=postcode, lat=lat, lng=lng)
            return redirect(url_for("dashboard"))

        # For display, reuse public fetch by id (barber-only route so safe)
        barber = get_barber_public_by_user_id(user_id)
        return render_template("pages/dashboard.html", barber=barber)