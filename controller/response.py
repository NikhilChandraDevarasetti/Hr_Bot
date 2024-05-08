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
from utils import fallback_handler
from utils import db_handler
from utils import db_response
import pandas as pd
from utils.logger import logger
from utils import config

event_logger = logger()

response_details = Blueprint("response", __name__)


@response_details.route("/display_response")
def display_response():
    """
    List of all Intents
    :return: Edit Intent View with
        data: Intent List(list)
        train: Count of Untrained Intents(string)
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    try:
        session["status"] = "response"
        all_intents = db_handler.fetch_all_intents()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("intent"),
                    x.get("response"),
                    x.get("query"),
                    x.get("entities"),
                    x.get("timestamp"),
                    db_handler.admin_user(x.get("user")),
                    x.get("status"),
                    x.get("_id"),
                ]
            )
        my_collection = db_connection["nlu_data"]
        train_collection = db_connection["train_data"]
        status_collection = db_connection["maintain_status"]
        status_data = my_collection.count_documents({"status": "2"})
        intent_status = status_collection.count_documents(
            {"name": "intent_status", "status": "1"})
        staging_data_count = train_collection.count_documents({})
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")

    try:
        if staging_data_count == 0:
            can_open = 1
        else:
            staging_data = train_collection.find().sort("_id", -1).limit(1)
            all_intents = []
            for x in staging_data:
                all_intents.append(x["approve_status"])
                all_intents.append(x["deploy"])
            if all_intents[1] == "1" or all_intents[1] == "3":
                can_open = 1
            else:
                if (
                    all_intents[0] == "1"
                    or all_intents[0] == "4"
                    or all_intents[0] == "5"
                ):
                    can_open = 1
                else:
                    can_open = 0

        return render_template(
            "admin/intent_list.html",
            data=_all_intents,
            train=status_data,
            can_open=can_open,
            intent_status=intent_status,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@response_details.route("/add_response")
def add_response():
    """
    Add New Response  - Add single Intent / Bulk Intent(Upload xslx)
    :return: Add Intent View / Intent list(list)/training Model List(List)
    """
    if session.get("islogin") != 1:
        return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    if "1" not in session.get("access"):
        return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    try:
        session["status"] = "add_response"
        return render_template("admin/add_response.html")
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@response_details.route("/add_single_response", methods=["POST"])
def add_single_response():
    try:
        projectpath = request.form
        x = db_response.insert_single_response(projectpath)
        return "hello"
        # return redirect(url_for('intent.bulk_intent_page', _external=True, _scheme= config['SSL_SECURITY']))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@response_details.route("/button_view", methods=["POST"])
def button_view():
    projectpath = request.form
    query_data = projectpath.to_dict(flat=False)
    cnt = query_data.pop("cnt")[0]
    _all_intents = []
    all_intents = db_handler.fetch_all_intents()
    for idx, x in enumerate(all_intents):
        _all_intents.append(
            [
                idx + 1,
                x.get("intent"),
            ]
        )
    return render_template(
        "user_input/dynamic_button.html", data_button=_all_intents, cnt=cnt
    )
