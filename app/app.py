from flask import Flask, render_template

def create_app():
    app = Flask(__name__)

    @app.get("/")
    def welcome():
        return render_template("welcome.html", title="Welcome Page")

    @app.get("/discover")
    def discover():
        return render_template("discover.html", title="Discover Page")

    @app.get("/barber_dashboard")
    def barber_dashboard():
        return render_template("barber_dashboard.html", title="Barber Dashboard")
    
    @app.route("/example")
    def example():
        return render_template("example.html", mount_id="photoUploadSingle", max_photos=1)

    return app

if __name__ == "__main__":
    create_app().run(debug=True)

