from functools import wraps
import pyotp
from flask import *
from flask_bootstrap import Bootstrap
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from faunadb.errors import BadRequest, Unauthorized

app = Flask(__name__)
Bootstrap(app)
app.config["SECRET_KEY"] = "APP_SECRET_KEY"
client = FaunaClient(secret="FAUNA_SECRET_KEY")


def get_user_details(user_secret):
    user_client = FaunaClient(secret=user_secret)
    user = user_client.query(
        q.current_identity()
    )
    user_details = client.query(
        q.get(
            q.ref(q.collection("users"), user.id())
        )
    )
    return user_details


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_secret" in session:
            try:
                user_client = FaunaClient(secret=session["user_secret"])
                result = user_client.query(
                    q.current_identity()
                )
            except Unauthorized as e:
                flash("Your login session has expired, please login again!", "danger")
                return redirect(url_for("login"))
        else:
            flash("You need to be logged in before you can access here!", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def auth_enrolled(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_details = get_user_details(session["user_secret"])
        if not user_details["data"]["auth_enrolled"]:
            return redirect(url_for("enroll_2fa"))
        return f(*args, **kwargs)

    return decorated


def auth_not_enrolled(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_details = get_user_details(session["user_secret"])
        if user_details["data"]["auth_enrolled"]:
            return redirect(url_for("verify_2fa"))
        return f(*args, **kwargs)

    return decorated


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        try:
            result = client.query(
                q.create(
                    q.collection("users"), {
                        "credentials": {"password": password},
                        "data": {
                            "email": email,
                            "auth_enrolled": False,
                            "auth_secret": pyotp.random_base32()
                        }
                    }
                )
            )
        except BadRequest as e:
            flash("The account you are trying to create already exists!", "danger")
            return redirect(url_for("register"))

        flash(
            "You have successfully created your account, you can proceed to login!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        try:
            result = client.query(
                q.login(
                    q.match(q.index("users_by_email"), email), {
                        "password": password}
                )
            )
        except BadRequest as e:
            flash(
                "You have supplied invalid login credentials, please try again!", "danger")
            return redirect(url_for("login"))

        session["user_secret"] = result["secret"]
        session["verified_2fa"] = False
        return redirect(url_for("verify_2fa"))

    return render_template("login.html")


@app.route("/2fa/enroll/", methods=["GET", "POST"])
@login_required
@auth_not_enrolled
def enroll_2fa():
    user_details = get_user_details(session["user_secret"])
    secret_key = user_details["data"]["auth_secret"]

    if request.method == "POST":
        otp = int(request.form.get("otp"))
        if pyotp.TOTP(secret_key).verify(otp):
            user_details["data"]["auth_enrolled"] = True
            client.query(
                q.update(
                    q.ref(q.collection("users"), user_details["ref"].id()), {
                        "data": user_details["data"]
                    }
                )
            )
            flash("You have successfully enrolled 2FA for your profile, please authenticate yourself once more!", "success")
            return redirect(url_for("verify_2fa"))
        else:
            flash("The OTP provided is invalid, it has either expired or was generated using a wrong SECRET!", "danger")
            return redirect(url_for("enroll_2fa"))

    return render_template("enroll_2fa.html", secret=secret_key)


@app.route("/2fa/verify/")
@login_required
@auth_enrolled
def verify_2fa():
    return render_template("verify_2fa.html")


@app.route("/logout/")
def logout():
    return "Logout Page!"


@app.route("/auth-success/")
def auth_success():
    return "<h1>Successfully authenticated account using Fauna and PyOTP!</h1>"


if __name__ == "__main__":
    app.run(debug=True)
