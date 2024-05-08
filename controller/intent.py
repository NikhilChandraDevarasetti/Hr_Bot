from flask import (
    render_template,
    request,
    session,
    redirect,
    Blueprint,
    Response,
    url_for,
)
import flask_paginate
from utils.db_connector import db_connection
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utils import fallback_handler
from utils import db_handler
from utils import create_dataset
import pandas as pd
import yaml
from utils.logger import logger
from utils import config
import json
from collections import OrderedDict

event_logger = logger()

intent_details = Blueprint("intent", __name__)

rows_per_page = 5


@intent_details.route("/display_intents")
def display_intents():
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
        session["status"] = "intent"
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
        page = request.args.get(
            flask_paginate.get_page_parameter(), type=int, default=1
        )
        offset = (page - 1) * rows_per_page
        x = (int(page) - 1) * rows_per_page
        y = int(page) * rows_per_page
        intents = _all_intents[x:y]
        pagination = flask_paginate.Pagination(
            page=page,
            per_page=rows_per_page,
            offset=offset,
            total=len(_all_intents),
            record_name="_all_intents",
            css_framework="bootstrap5",
        )

        return render_template(
            "admin/intent_list.html",
            data=intents,
            train=status_data,
            can_open=can_open,
            intent_status=intent_status,
            pagination=pagination,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/bulk_intent")
def bulk_intent_page():
    """
    Add New Intent  - Add single Intent / Bulk Intent(Upload xslx)
    :return: Add Intent View / Intent list(list)/training Model List(List)
    """
    if session.get("islogin") != 1:
        return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    if "1" not in session.get("access"):
        return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    try:
        session["status"] = "add"
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
                    x.get("user"),
                    x.get("status"),
                    x.get("_id"),
                ]
            )
        all_training = db_handler.fetch_training_model()
        _all_training = []
        for id_x, y in enumerate(all_training):
            _all_training.append(
                [
                    id_x + 1,
                    y.get("model_profile_name"),
                    y.get("status"),
                    y.get("timestamp"),
                    y.get("trained_by"),
                ]
            )
        return render_template(
            "admin/bulk_intent.html", data=_all_intents, train_data=_all_training
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/add_single_intent", methods=["POST"])
def add_single_intent():
    """
    Add Single Intent and redirect to Add Form
    :return: Redirect to Add Form View
    """
    try:
        x = db_handler.insert_single_intent(request)
        return redirect(
            url_for("intent.bulk_intent_page", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/add_multiple_intents", methods=["POST"])
def add_multiple_intents():
    """
    :Input: XLSX File
    Add Bulk Intent and redirect to Add Form
    :return: Redirect to Add Form View
    """
    try:
        form_data = request.form.to_dict(flat=False)
        now = datetime.now()
        schedule_time = now + timedelta(minutes=5)
        if form_data.get("schedule_training") == "schedule":
            schedule_time = form_data.get("train_schedule_date")
        intent_file = request.files
        data = db_handler.insert_multiple_intent(intent_file, schedule_time)
        if data == "error":
            return redirect(
                url_for("intent.bulk_intent_page", _external=True, _scheme=config.SSL_SECURITY)
            )
        else:
            return redirect(
                url_for("intent.bulk_intent_page", _external=True, _scheme=config.SSL_SECURITY)
            )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/replace/intent")
def edit_intent():
    """
    Edit Intent details
    :id: Intent Object Id
    :return: Edit Intent View with
        data: Intent Details
        x_data: Intent Example List
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    try:
        if "1" not in session.get("access"):
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")

    try:
        session["status"] = "intent"
        id_ = request.args.get("id")
        my_collection = db_connection["nlu_data"]
        all_db_intents = my_collection.find({"_id": ObjectId(id_)})
        all_intents = []
        for x in all_db_intents:
            all_intents.append(x["intent"])
            all_intents.append(x["response"][0])
            all_intents.append(x["query"][0])
            all_intents.append(x["description"][0])
            all_intents.append(x["_id"])
            all_intents.append(x["nlu_id"])
        query_data = my_collection.find({"_id": ObjectId(id_)}, {"query": 1})
        x_data = []
        for id, y in enumerate(query_data):
            x_data.append(y["query"])
        res_data = my_collection.find({"_id": ObjectId(id_)}, {"response": 1})
        r_data = []
        for id, r in enumerate(res_data):
            r_data.append(r["response"])
        len_res_data = str(len(r_data[0]) - 1)
        len_query_data = str(len(x_data[0]) - 1)
        return render_template(
            "admin/edit_intent.html",
            data=all_intents,
            x_data=x_data[0],
            r_data=r_data[0],
            len_query_data=len_query_data,
            len_res_data=len_res_data,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/update_intent", methods=["POST"])
def update_intent():
    """
    Update Intent Data and Redirect to Intent List
    :return: Redirect to Intent List View
    """
    try:
        projectpath = request.form
        db_handler.update_single_intent(projectpath)
        return redirect(
            url_for("intent.display_intents", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/check_intent", methods=["POST"])
def check_intent():
    """
    Validation function Check Intent is present or not(Unique)
    :return: Intent Count String
    """
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        intent = query_data.pop("answer1")[0]
        my_collection = db_connection["nlu_data"]
        intent_count = my_collection.count_documents({"intent": intent})
        return str(intent_count)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/check_intent_duplicat", methods=["POST"])
def check_intent_duplicat():
    """
    Validation function Check Intent is present or not(Unique)
    :return: Intent Count String
    """
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        intent = query_data.pop("answer1")[0]
        nlu_id = query_data.pop("answer4")[0]
        my_collection = db_connection["nlu_data"]
        intent_count = my_collection.count_documents({"intent": intent})
        intent_list = my_collection.find({"intent": intent})
        all_intents = []
        if intent_count > 0:
            for x in intent_list:
                all_intents.append(x["nlu_id"])
            intent_name = all_intents[0]
            if intent_name == nlu_id:
                return str(0)
            else:
                return str(1)
        else:
            return str(0)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")


@intent_details.route("/download_intents")
def download_intents():
    """
    Download All Intent In csv Format
    :return: Return CSV(All Intent List)
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")

    try:
        my_collection = db_connection["nlu_data"]
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
                "Content-disposition": f"attachment; filename=HRbot_intents_{timestamp}.csv"
            },
        )
        return resp

    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/intent")
def intents():
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
        return render_template("admin/401.html")

    try:
        session["status"] = "intent"
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
                    x.get("nlu_id"),
                ]
            )
        my_collection = db_connection["nlu_data"]
        status_data = my_collection.count_documents({"status": "2"})
        return render_template(
            "admin/intent.html", data=_all_intents, train=status_data
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/intent_mapping")
def intent_mapping():

    if session.get("islogin") != 1:
        return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    if "5" not in session.get("access"):
        return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    try:
        fallback_handler.fetch_mismatch_chats()
        session["status"] = "intent_mapping"
        all_intents = db_handler.fetch_mismatch_intent()
        intents_list = db_handler.fetch_all_intents()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append([idx + 1, x.get("query"), x.get("q_id")])
        intents_data = []
        for idx, y in enumerate(intents_list):
            intents_data.append(
                [
                    str(y.get("intent")),
                    str(y.get("nlu_id")),
                ]
            )

        page = request.args.get(
            flask_paginate.get_page_parameter(), type=int, default=1
        )
        offset = (page - 1) * rows_per_page
        x = (int(page) - 1) * rows_per_page
        y = int(page) * rows_per_page
        data = _all_intents[x:y]
        pagination = flask_paginate.Pagination(
            page=page,
            per_page=rows_per_page,
            offset=offset,
            total=len(_all_intents),
            record_name="_all_intents",
            css_framework="bootstrap5",
        )

        return render_template(
            "admin/intent_mapping.html",
            data=data,
            x_data=intents_data,
            pagination=pagination,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/map_intent", methods=["POST"])
def map_intent():
    try:
        my_collection = db_connection["fallback_queries"]
        nlu_collection = db_connection["nlu_data"]
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        q_id = query_data.pop("q_id")[0]
        intent_id = query_data.pop("intent_id")[0]

        all_db_intents = my_collection.find({"q_id": q_id})
        for x in all_db_intents:
            nlu_collection.update_one(
                {"nlu_id": str(intent_id)}, {"$push": {"query": x["query"]}}
            )
        my_collection.update_one({"q_id": q_id}, {"$set": {"status": "1"}}, True)
        return q_id
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/all_chats")
def all_chats():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    try:
        if "5" not in session.get("access"):
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")

    try:
        session["status"] = "intent_mapping"
        all_intents = db_handler.fetch_mismatch_intent()
        intents_list = db_handler.fetch_all_intents()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append([idx + 1, x.get("query"), x.get("q_id")])
        intents_data = []
        for idx, y in enumerate(intents_list):
            intents_data.append(
                [
                    str(y.get("intent")),
                    str(y.get("nlu_id")),
                ]
            )
        return render_template(
            "admin/intent_mapping.html", data=_all_intents, x_data=intents_data
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/intent_map_list")
def intent_map_list():
    try:
        fallback_handler.fetch_mismatch_chats()
        return redirect(
            url_for("intent.intent_mapping", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")


@intent_details.route("/chat_list")
def chat_list():
    try:
        if "6" not in session.get("access"):
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")
    try:
        session["status"] = "chat_list"
        all_data = fallback_handler.fetch_chats()
        data = []
        for idx, x in enumerate(all_data):
            data.append(
                [
                    idx + 1,
                    x.get("queries"),
                    x.get("response"),
                    x.get("intent"),
                ]
            )

        page = request.args.get(
            flask_paginate.get_page_parameter(), type=int, default=1
        )
        offset = (page - 1) * rows_per_page
        x = (int(page) - 1) * rows_per_page
        y = int(page) * rows_per_page
        chat_data = data[x:y]
        pagination = flask_paginate.Pagination(
            page=page,
            per_page=rows_per_page,
            offset=offset,
            total=len(data),
            record_name="chat_list",
            css_framework="bootstrap5",
        )

        return render_template(
            "admin/chat_list.html", data=chat_data, pagination=pagination
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/model_intent_list", methods=["POST"])
def model_intent_list():
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        model_id = query_data.get("model_id")[0]
        model_name = query_data.get("name")[0]
        train_collection = db_connection["train_data"]
        nlu_collection = db_connection["nlu_data"]
        all_db_intents = train_collection.find(
            {"model_id": model_id}, {"newly_train_intents": 1}
        )
        all_intents = []
        if not all_db_intents:
            newly_train_intents = []
        else:
            for x in all_db_intents:
                all_intents.append(x["newly_train_intents"])
            newly_train_intents = all_intents[0]
        nlu_details = nlu_collection.find({"nlu_id": {"$in": newly_train_intents}})
        _nlu_intents = []
        for idx, x in enumerate(nlu_details):
            _nlu_intents.append(
                [
                    idx + 1,
                    x.get("intent"),
                    x.get("nlu_id"),
                ]
            )
        return render_template(
            "admin/intent_rejection.html",
            data=_nlu_intents,
            model_name=model_name,
            model_id=model_id,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/delete_intent", methods=["POST"])
def delete_intent():
    """
    Delete Intent Data and Redirect to Intent List
    :return: Redirect to Intent List View
    """
    try:
        projectpath = request.form
        db_handler.delete_single_intent(projectpath)
        return redirect(
            url_for("intent.display_intents", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/delete_all_intent", methods=["POST"])
def delete_all_intent():
    """
    Delete All Intent Data and Redirect to Intent List
    :return: Redirect to Intent List View-
    """
    try:
        db_handler.delete_all_intent()
        return redirect(
            url_for("intent.display_intents", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@intent_details.route("/intent_res", methods=["POST"])
def intent_res():
    projectpath = request.form
    query_data = projectpath.to_dict(flat=False)
    res_type = query_data.pop("res_type")[0]
    _all_intents = []
    if res_type == "2":
        all_intents = db_handler.fetch_all_intents()
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("intent"),
                ]
            )
    return render_template(
        "user_input/text_res.html", data=res_type, data_button=_all_intents
    )
