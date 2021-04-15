from flask import *
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register/")
def register():
    return "Register Page!"


if __name__ == "__main__":
    app.run(debug=True)
