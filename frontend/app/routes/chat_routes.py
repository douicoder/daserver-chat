from flask import Blueprint, render_template, session, redirect, url_for, request, Response, current_app

chat_bp = Blueprint("chat", __name__)


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "access_token" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@chat_bp.route("/chat")
@login_required
def index():
    user = session.get("user", {})
    return render_template("chat.html", user=user)


@chat_bp.route("/admin")
@login_required
def admin_page():
    user = session.get("user", {})
    if not user.get("is_admin"):
        return redirect(url_for("chat.index"))
    return render_template("admin.html", user=user)


@chat_bp.route("/attachments/<attachment_id>")
@login_required
def proxy_attachment(attachment_id):
    """Proxy attachment downloads through the frontend so the browser doesn't
    need to send the backend JWT itself.

    The chat UI links to this same-origin URL (session cookie auth). We attach
    the backend Bearer token server-side and stream the file back. Images/PDFs
    display inline; everything else downloads.
    """
    import requests

    token = session.get("access_token", "")
    if not token:
        return redirect(url_for("auth.login"))

    backend_url = current_app.config["BACKEND_URL"].rstrip("/")
    try:
        resp = requests.get(
            f"{backend_url}/api/attachments/{attachment_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"download": request.args.get("download", "")} if request.args.get("download") else None,
            stream=True,
            timeout=30,
        )
    except requests.RequestException:
        return Response("Unable to reach file server.", status=502)

    if resp.status_code != 200:
        try:
            body = resp.json()
            msg = (body.get("error") or {}).get("message", "File unavailable.")
        except Exception:
            msg = "File unavailable."
        return Response(msg, status=resp.status_code)

    mime = resp.headers.get("Content-Type", "application/octet-stream")
    # Preserve backend filename when present, else fall back to id.
    filename = attachment_id
    cd = resp.headers.get("Content-Disposition", "")
    if "filename" in cd:
        try:
            filename = cd.split("filename")[1].strip(" *=;\"'")
            if not filename:
                filename = attachment_id
        except Exception:
            pass

    # Inline for viewable types so clicking opens/previews; force download with ?download=1.
    force_download = request.args.get("download") == "1"
    inline_types = ("image/", "application/pdf", "text/plain")
    disp = "attachment" if (force_download or not mime.startswith(inline_types)) else "inline"

    def generate():
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    headers = {"Content-Disposition": f'{disp}; filename="{filename}"'}
    return Response(generate(), mimetype=mime, headers=headers)
