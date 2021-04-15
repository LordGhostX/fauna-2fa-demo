from flask import *
from flask_bootstrap import Bootstrap
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from faunadb.errors import BadRequest

app = Flask(__name__)
Bootstrap(app)
app.config["SECRET_KEY"] = "APP_SECRET_KEY"
client = FaunaClient(secret="FAUNA_SECRET_KEY")


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
                        "data": {"email": email}
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


@app.route("/auth-success/")
def auth_success():
    return "<h1>Successfully authenticated account using Fauna and PyOTP!</h1>"


if __name__ == "__main__":
    app.run(debug=True)
