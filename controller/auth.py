from flask import (
    render_template,
    request,
    session,
    redirect,
    Blueprint,
    Response,
    url_for,
)

admin_auth = Blueprint("auth", __name__)
from utils.logger import logger
from utils import config
event_logger = logger()


@admin_auth.route("/login")
def login():
    """
    Admin Login
    :return: Login Page View
    """
    try:
        return render_template("admin/login.html")
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/502.html")



@admin_auth.route("/sign_out")
def sign_out():
    """
    User Logout
    :return: Redirect to Login View
    """
    session.clear()
    return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))