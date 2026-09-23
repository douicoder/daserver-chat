from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from app.services.backend_client import BackendClient

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username:
        return render_template("login.html", error="Username is required.", username=username)
    if not password:
        return render_template("login.html", error="Password is required.", username=username)

    client = BackendClient()
    status, body = client.login(username, password)

    if status == 200 and body and "access_token" in body:
        session["access_token"] = body["access_token"]
        session["user"] = body["user"]
        return redirect(url_for("chat.index"))

    error_msg = "Invalid username or password."
    if body and "error" in body:
        error_msg = body["error"].get("message", error_msg)
    return render_template("login.html", error=error_msg, username=username)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not username:
        return render_template("register.html", error="Username is required.", username=username)
    if not password:
        return render_template("register.html", error="Password is required.", username=username)
    if len(password) < 6:
        return render_template("register.html", error="Password must be at least 6 characters.", username=username)
    if password != confirm_password:
        return render_template("register.html", error="Passwords do not match.", username=username)

    client = BackendClient()
    status, body = client.register(username, password)

    if status == 201 and body and "access_token" in body:
        session["access_token"] = body["access_token"]
        session["user"] = body["user"]
        return redirect(url_for("chat.index"))

    error_msg = "Registration failed."
    if body and "error" in body:
        error_msg = body["error"].get("message", error_msg)
    return render_template("register.html", error=error_msg, username=username)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/")
def index():
    if "access_token" in session:
        return redirect(url_for("chat.index"))
    return redirect(url_for("auth.login"))
