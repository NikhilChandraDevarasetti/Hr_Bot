from flask import (
    render_template,
    request,
    session,
    redirect,
    Blueprint,
    Response,
    url_for,
)
from utils.create_dataset import get_training_set
from utils import rasa_wrapper as rasa_wrapper
from utils.db_connector import db_connection
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utils import super_admin_model
from utils import db_handler
import pandas as pd
import threading
import shutil
import os
from utils.logger import logger
from utils import config

event_logger = logger()

admin_details = Blueprint("admin", __name__)


@admin_details.route("/admin")
def dashboard():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    try:
        session["status"] = "admin_dashboard"
        # Intent Details
        nlu_collection = db_connection["nlu_data"]
        nlu_data_trained = nlu_collection.count_documents({"status": "1"})
        nlu_data_untrained = nlu_collection.count_documents({"status": "2"})
        nlu_data_total = nlu_collection.count_documents({})
        prod_count = ""
        prod_name = ""
        stag_count = ""
        stag_name = ""
        # Production model
        train_collection = db_connection["train_data"]
        prod_count_total = train_collection.count_documents({"deploy": "1"})
        prod_count_total_both = train_collection.count_documents({"deploy": "3"})
        if prod_count_total > 0:
            prod_mod = train_collection.find({"deploy": "1"})
            x = []
            for i in prod_mod:
                x.append(i.get("model_profile_name"))
                x.append(i.get("intent_list"))
            prod_count = str(len(x[1]))
            prod_name = x[0]
        elif prod_count_total_both > 0:
            prod_mod = train_collection.find({"deploy": "3"})
            x = []
            for i in prod_mod:
                x.append(i.get("model_profile_name"))
                x.append(i.get("intent_list"))
            prod_count = str(len(x[1]))
            prod_name = x[0]
        else:
            prod_name = ""
            prod_count = ""
        # Staging Model
        stag_count_total = train_collection.count_documents({"deploy": "2"})
        stag_count_total_both = train_collection.count_documents({"deploy": "3"})
        if stag_count_total > 0:
            stag_mod = train_collection.find({"deploy": "2"})
            y = []
            for j in stag_mod:
                y.append(j.get("model_profile_name"))
                y.append(j.get("intent_list"))
            stag_count = str(len(y[1]))
            stag_name = y[0]
        elif stag_count_total_both > 0:
            stag_mod = train_collection.find({"deploy": "3"})
            y = []
            for j in stag_mod:
                y.append(j.get("model_profile_name"))
                y.append(j.get("intent_list"))
            stag_count = str(len(y[1]))
            stag_name = y[0]
        else:
            stag_name = ""
            stag_count = ""
        # User Details
        user_collection = db_connection["admin_login"]
        user_active = user_collection.count_documents({"status": "1"})
        user_inactive = user_collection.count_documents({"status": "0"})
        user_total = user_collection.count_documents({})

        # Role Details
        role_collection = db_connection["admin_role"]
        role_total = role_collection.count_documents({})

        return render_template(
            "super_admin/dashboard.html",
            role_total=role_total,
            user_total=user_total,
            user_active=user_active,
            user_inactive=user_inactive,
            nlu_data_trained=nlu_data_trained,
            nlu_data_untrained=nlu_data_untrained,
            nlu_data_total=nlu_data_total,
            prod_name=prod_name,
            prod_count=prod_count,
            stag_name=stag_name,
            stag_count=stag_count,
            prod_socket_uri=config.PROD_SOCKET_URI,
            prod_socket_path=config.PROD_SOCKET_PATH,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")


@admin_details.route("/admin/testing")
def testing():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    session["status"] = "testing"
    return render_template(
        "super_admin/testing.html",
        prod_socket_uri=config.PROD_SOCKET_URI,
        prod_socket_path=config.PROD_SOCKET_PATH,
    )


@admin_details.route("/admin/user_list")
def user_list():
    """
    List of all Intents
    :return: Edit Intent View with
        data: Intent List(list)
        train: Count of Untrained Intents(string)
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    try:
        session["status"] = "User List"
        all_users = super_admin_model.fetch_all_user()
        _all_users = []
        for idx, x in enumerate(all_users):
            _all_users.append(
                [
                    idx + 1,
                    x.get("name"),
                    x.get("username"),
                    x.get("email"),
                    fetch_role(x.get("role")),
                    x.get("_id"),
                    x.get("timestamp"),
                    x.get("admin_id"),
                    x.get("role"),
                    x.get("password"),
                ]
            )
        return render_template("super_admin/user_list.html", data=_all_users)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/fetch_role")
def fetch_role(id):
    try:
        role_collection = db_connection["admin_role"]
        role_data = role_collection.find({"role_id": id})
        x_data = []
        for id, y in enumerate(role_data):
            x_data.append(y["role"])
        return x_data[0]
    except Exception as e:
        return render_template("admin/404.html")


@admin_details.route("/admin/add_user", methods=["POST", "GET"])
def add_user():
    """
    Add New User Form
    :return: Add User View
    """
    try:
        if request.method == "POST":
            projectpath = request.form
            super_admin_model.insert_user(projectpath)
            print('welcome')
            return redirect(url_for("admin.user_list", _external=True, _scheme=config.SSL_SECURITY))
        else:
            if session.get("islogin") != 1 and session.get("role") != "1":
                return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
            session["status"] = "add_user"
            admin_collection = db_connection["admin_role"]
            all_db_intents = admin_collection.find().sort("_id", -1)
            all_roles = []
            for idx, x in enumerate(all_db_intents):
                all_roles.append(
                    [
                        idx + 1,
                        x.get("role"),
                        x.get("role_id"),
                    ]
                )
            return render_template("super_admin/add_user.html", x_data=all_roles)
    except Exception as e:
        event_logger.error(e)
        print(str(e))
        return render_template("admin/500.html")


@admin_details.route("/admin/update_user", methods=["POST", "GET"])
def update_user():
    """
    Edit Intent details
    :id: Intent Object Id
    :return: Edit Intent View with
        data: Intent Details
        x_data: Intent Example List
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
        session["status"] = "Add User"
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    try:
        if request.method == "POST":
            projectpath = request.form
            super_admin_model.update_user(projectpath)
            return redirect(url_for("admin.user_list", _external=True, _scheme= config.SSL_SECURITY))
        else:
            id_ = request.args.get("id")
            admin_collection = db_connection["admin_login"]
            role_collection = db_connection["admin_role"]
            all_db_intents = admin_collection.find({"admin_id": id_})
            all_intents = []
            for x in all_db_intents:
                all_intents.append(x["name"])
                all_intents.append(x["username"])
                all_intents.append(x["email"])
                all_intents.append(x["role"])
                all_intents.append(x["admin_id"])
                all_intents.append(x["password"])
            all_db = role_collection.find().sort("_id", -1)
            all_roles = []
            for idx, x in enumerate(all_db):
                all_roles.append(
                    [
                        idx + 1,
                        x.get("role"),
                        x.get("role_id"),
                    ]
                )
        return render_template(
            "super_admin/update_user.html", data=all_intents, x_data=all_roles
        )
    except Exception as e:
        event_logger.error(e)
        print(str(e))
        return render_template("admin/404.html")


@admin_details.route("/author")
def author_dashboard():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
        session["status"] = "dashboard"

    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")

    # Intent Details
    try:
        nlu_collection = db_connection["nlu_data"]
        nlu_data_trained = nlu_collection.count_documents({"status": "1"})
        nlu_data_untrained = nlu_collection.count_documents({"status": "2"})
        nlu_data_total = nlu_collection.count_documents({})
        prod_count = ""
        prod_name = ""
        stag_count = ""
        stag_name = ""
        # Production model
        train_collection = db_connection["train_data"]
        prod_count_total = train_collection.count_documents({"deploy": "1"})
        prod_count_total_both = train_collection.count_documents({"deploy": "3"})
        if prod_count_total > 0:
            prod_mod = train_collection.find({"deploy": "1"})
            x = []
            for i in prod_mod:
                x.append(i.get("model_profile_name"))
                x.append(i.get("intent_list"))
            prod_count = str(len(x[1]))
            prod_name = x[0]
        elif prod_count_total_both > 0:
            prod_mod = train_collection.find({"deploy": "3"})
            x = []
            for i in prod_mod:
                x.append(i.get("model_profile_name"))
                x.append(i.get("intent_list"))
            prod_count = str(len(x[1]))
            prod_name = x[0]
        else:
            prod_name = ""
            prod_count = ""

        # Staging Model
        stag_count_total = train_collection.count_documents({"deploy": "2"})
        stag_count_total_both = train_collection.count_documents({"deploy": "3"})
        if stag_count_total > 0:
            stag_mod = train_collection.find({"deploy": "2"})
            y = []
            for j in stag_mod:
                y.append(j.get("model_profile_name"))
                y.append(j.get("intent_list"))
            stag_count = str(len(y[1]))
            stag_name = y[0]
        elif stag_count_total_both > 0:
            stag_mod = train_collection.find({"deploy": "3"})
            y = []
            for j in stag_mod:
                y.append(j.get("model_profile_name"))
                y.append(j.get("intent_list"))
            stag_count = str(len(y[1]))
            stag_name = y[0]
        else:
            stag_name = ""
            stag_count = ""
        # Pending List
        all_intents = db_handler.fetch_pending_model()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test_pend(x.get("model_id"), "1", "stage"),
                    active_count_test_pend(x.get("model_id"), "0", "stage"),
                    active_count_test_pend(x.get("model_id"), "1", "prod"),
                    active_count_test_pend(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )
        return render_template(
            "admin/author_dashboard.html",
            nlu_data_trained=nlu_data_trained,
            nlu_data_untrained=nlu_data_untrained,
            nlu_data_total=nlu_data_total,
            data=_all_intents,
            prod_name=prod_name,
            prod_count=prod_count,
            stag_name=stag_name,
            stag_count=stag_count,
            prod_socket_uri=config.PROD_SOCKET_URI,
            prod_socket_path=config.PROD_SOCKET_PATH,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/active_count_test_pend")
def active_count_test_pend(model_id, status, evn):
    try:
        my_collection = db_connection["train_data"]
        nlu_collection = db_connection["nlu_data"]
        all_db_intents = my_collection.find({"model_id": model_id}, {"intent_list": 1})
        all_intents = []
        if not all_db_intents:
            intent_list = []
        else:
            for x in all_db_intents:
                all_intents.append(x["intent_list"])
            intent_list = all_intents[0]
        nlu_data = ""
        if status == "1" and evn == "stage":
            nlu_data = nlu_collection.count_documents(
                {"s_status": "1", "nlu_id": {"$in": intent_list}})
        elif status == "0" and evn == "stage":
            nlu_data = nlu_collection.count_documents(
                {"s_status": "0", "nlu_id": {"$in": intent_list}})
        elif status == "1" and evn == "prod":
            nlu_data = nlu_collection.count_documents(
                {"p_status": "1", "nlu_id": {"$in": intent_list}})
        elif status == "0" and evn == "prod":
            nlu_data = nlu_collection.count_documents(
                {"p_status": "0", "nlu_id": {"$in": intent_list}})
        return str(nlu_data)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")


@admin_details.route("/user_chat")
def user_chat():
    """
    Staging Environment for testing
    :return: Staging Environment View
    """
    if session.get("islogin") != 1:
        return redirect(url_for('auth.login', _external=True, _scheme= config.SSL_SECURITY))
    return render_template("admin/res_bot.html")


@admin_details.route("/mobile_chat")
def mobile_chat():
    """
    Staging Environment for testing
    :return: Staging Environment View
    """
    # print("user_chat")
    # print(session.__dict__)
    if session.get("islogin") != 1:
        return redirect(url_for('auth.login', _external=True, _scheme=config.SSL_SECURITY))
    return render_template("admin/mobile_view.html")


@admin_details.route("/approver")
def approver_dashboard():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config['SSL_SECURITY']))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    try:
        session["status"] = "dashboard"
        # Intent Details
        nlu_collection = db_connection["nlu_data"]
        nlu_data_trained = nlu_collection.count_documents({"status": "1"})
        nlu_data_untrained = nlu_collection.count_documents({"status": "2"})
        nlu_data_total = nlu_collection.count_documents({})
        prod_count = ""
        prod_name = ""
        stag_count = ""
        stag_name = ""
        # Production model
        train_collection = db_connection["train_data"]
        prod_count_total = train_collection.count_documents({"deploy": "1"})
        prod_count_total_both = train_collection.count_documents({"deploy": "3"})
        if prod_count_total > 0:
            prod_mod = train_collection.find({"deploy": "1"})
            x = []
            for i in prod_mod:
                x.append(i.get("model_profile_name"))
                x.append(i.get("intent_list"))
            prod_count = str(len(x[1]))
            prod_name = x[0]
        elif prod_count_total_both > 0:
            prod_mod = train_collection.find({"deploy": "3"})
            x = []
            for i in prod_mod:
                x.append(i.get("model_profile_name"))
                x.append(i.get("intent_list"))
            prod_count = str(len(x[1]))
            prod_name = x[0]
        else:
            prod_name = ""
            prod_count = ""

        # Staging Model
        stag_count_total = train_collection.count_documents({"deploy": "2"})
        stag_count_total_both = train_collection.count_documents({"deploy": "3"})
        if stag_count_total > 0:
            stag_mod = train_collection.find({"deploy": "2"})
            y = []
            for j in stag_mod:
                y.append(j.get("model_profile_name"))
                y.append(j.get("intent_list"))
            stag_count = str(len(y[1]))
            stag_name = y[0]
        elif stag_count_total_both > 0:
            stag_mod = train_collection.find({"deploy": "3"})
            y = []
            for j in stag_mod:
                y.append(j.get("model_profile_name"))
                y.append(j.get("intent_list"))
            stag_count = str(len(y[1]))
            stag_name = y[0]
        else:
            stag_name = ""
            stag_count = ""
        # Pending List
        all_intents = db_handler.fetch_pending_model()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test_pend(x.get("model_id"), "1", "stage"),
                    active_count_test_pend(x.get("model_id"), "0", "stage"),
                    active_count_test_pend(x.get("model_id"), "1", "prod"),
                    active_count_test_pend(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )
        return render_template(
            "admin/approver_dashboard.html",
            nlu_data_trained=nlu_data_trained,
            nlu_data_untrained=nlu_data_untrained,
            nlu_data_total=nlu_data_total,
            data=_all_intents,
            prod_name=prod_name,
            prod_count=prod_count,
            stag_name=stag_name,
            stag_count=stag_count,
            prod_socket_uri=config.PROD_SOCKET_URI,
            prod_socket_path=config.PROD_SOCKET_PATH,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/check_username", methods=["POST"])
def check_username():
    """
    Validation function Check Intent is present or not(Unique)
    :return: admin username Count String
    """
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        admin = query_data.pop("answer2")[0]
        admin_collection = db_connection["admin_login"]
        admin_count = admin_collection.count_documents({"username": admin})
        return str(admin_count)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/check_email", methods=["POST"])
def check_email():
    """
    Validation function Check Intent is present or not(Unique)
    :return: admin email Count String
    """
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        admin = query_data.pop("answer3")[0]
        admin_collection = db_connection["admin_login"]
        admin_count = admin_collection.count_documents({"email": admin})
        return str(admin_count)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/download_admin")
def download_admin():
    """
    Download All Intent In csv Format
    :return: Return CSV(All Admin List)
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config['SSL_SECURITY']))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    try:
        my_collection = db_connection["admin_login"]
        cursor = my_collection.find({})
        df = pd.json_normalize(cursor)
        timestamp = str(datetime.now().replace(microsecond=0).isoformat("_"))
        csv_file = df.to_csv(
            encoding="utf-8",
            index=False,
        )
        resp = Response(
            csv_file,
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; filename=Chat_user_{timestamp}.csv"
            },
        )
        return resp
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/admin/delete_user", methods=["POST", "GET"])
def delete_user():
    """
    Edit Intent details
    :id: Intent Object Id
    :return: Edit Intent View with
        data: Intent Details
        x_data: Intent Example List
    """
    if session.get("islogin") != 1:
        return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
    try:
        session["status"] = "Add User"
        id_ = request.args.get("id")
        admin_collection = db_connection["admin_login"]
        updated_values = {
            "$set": {
                "status": "0",
            }
        }
        queries = {"admin_id": id_}
        _id = admin_collection.remove(queries)
        return redirect(url_for("admin.user_list", _external=True, _scheme= config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        print(str(e))
        return render_template("admin/500.html")


@admin_details.route("/admin/role_list")
def role_list():
    """
    List of all Roles
    :return: List of Admin Role View with
        data: Role List(list)
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))

    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    try:
        session["status"] = "User Role"
        all_users = super_admin_model.fetch_all_role()
        _all_users = []
        for idx, x in enumerate(all_users):
            _all_users.append(
                [
                    idx + 1,
                    x.get("role"),
                    super_admin_model.admin_role_access(x.get("access")),
                    x.get("access"),
                    x.get("role_id"),
                ]
            )
        return render_template("super_admin/role_list.html", data=_all_users)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/admin/add_role", methods=["POST", "GET"])
def add_role():
    """
    Add New Role Form
    :return: Add Role View
    """
    try:
        if request.method == "POST":
            projectpath = request.form
            super_admin_model.insert_role(projectpath)
            return redirect(url_for("admin.role_list", _external=True, _scheme= config.SSL_SECURITY))
        else:
            if session.get("islogin") != 1 and session.get("role") != "1":
                return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
            session["status"] = "add_role"

            return render_template("super_admin/add_role.html")
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/admin/update_role", methods=["POST", "GET"])
def update_role():
    """
    Edit Intent details
    :id: Intent Object Id
    :return: Edit Intent View with
        data: Intent Details
        x_data: Intent Example List
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")

    session["status"] = "Add Role"

    try:
        if request.method == "POST":
            projectpath = request.form
            super_admin_model.update_role(projectpath)
            return redirect(url_for("admin.role_list", _external=True, _scheme= config.SSL_SECURITY))
        else:
            id_ = request.args.get("id")
            admin_collection = db_connection["admin_role"]
            all_db_intents = admin_collection.find({"role_id": id_})
            all_access = admin_collection.find({"role_id": id_}, {"access": 1})
            all_intents = []
            for x in all_db_intents:
                all_intents.append(x["role"])
                all_intents.append(x["role_id"])
            x_data = []
            for id, y in enumerate(all_access):
                x_data.append(y["access"])
        return render_template(
            "super_admin/update_role.html", data=all_intents, x_data=x_data[0]
        )

    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@admin_details.route("/download_role")
def download_role():
    """
    Download All Intent In csv Format
    :return: Return CSV(All Admin List)
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme= config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    try:
        my_collection = db_connection["admin_role"]
        cursor = my_collection.find({})
        df = pd.json_normalize(cursor)
        timestamp = str(datetime.now().replace(microsecond=0).isoformat("_"))
        csv_file = df.to_csv(
            encoding="utf-8",
            index=False,
        )
        resp = Response(
            csv_file,
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; filename=Chat_role_{timestamp}.csv"
            },
        )
        return resp
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")
