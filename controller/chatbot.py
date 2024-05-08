from flask import (
    render_template,
    request,
    session,
    redirect,
    Blueprint,
    Response,
    url_for,
)
from utils.db_connector import db_connection
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utils import config
import pandas as pd
from utils.logger import logger

event_logger = logger()


chatbot_details = Blueprint("chatbot", __name__)


@chatbot_details.route("/chatbot/login")
def login():
    """
    Admin Login
    :return: Login Page View
    """
    try:
        return render_template("frontend/login.html")
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/502.html")


@chatbot_details.route("/chatbot/admin_login", methods=["POST"])
def admin_login():
    """
    Check User Authentication
    :return: Redirect Dashboard View
    """
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        username = query_data.pop("username")[0]
        password = query_data.pop("password")[0]
        my_collection = db_connection["admin_login"]
        checkuser = my_collection.count_documents(
            {"username": username, "password": password})
        if checkuser > 0:
            user = my_collection.find({"username": username, "password": password})
            user_details = []
            for x in user:
                user_details.append(x["email"])
                user_details.append(x["role"])
                user_details.append(x["admin_id"])
            session["islogin"] = 1
            session["username"] = username
            session["admin_id"] = user_details[2]
            session["role"] = user_details[1]
            # if user_details[1] == "1":
            #     return redirect(url_for('admin.dashboard', _external=True, _scheme= config['SSL_SECURITY']))
            # elif user_details[1] == "2":
            #     return redirect(url_for('admin.author', _external=True, _scheme= config['SSL_SECURITY']))
            # elif user_details[1] == "3":
            #     return redirect(url_for('admin.approver', _external=True, _scheme= config['SSL_SECURITY']))
            # else:
            return redirect(
                url_for("chatbot.dashboard", _external=True, _scheme=config.SSL_SECURITY)
            )
        else:
            return redirect(url_for("chatbot.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@chatbot_details.route("/chatbot/sign_out")
def sign_out():
    """
    User Logout
    :return: Redirect to Login View
    """
    session.clear()
    return redirect(url_for("chatbot.login", _external=True, _scheme=config.SSL_SECURITY))


@chatbot_details.route("/chatbot")
def dashboard():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
        session["status"] = "admin_dashboard"
        return render_template(
            "frontend/dashboard.html",
            prod_socket_uri=config.PROD_SOCKET_URI,
            prod_socket_path=config.PROD_SOCKET_PATH,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
