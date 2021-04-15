from flask import *
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register/")
def register():
    return render_template("register.html")


@app.route("/login/")
def login():
    return render_template("login.html")


@app.route("/2fa/enroll/")
def enroll_2fa():
    return render_template("enroll_2fa.html")


@app.route("/2fa/verify/")
def verify_2fa():
    return render_template("verify_2fa.html")


@app.route("/logout/")
def logout():
    return "Logout Page!"


if __name__ == "__main__":
    app.run(debug=True)
