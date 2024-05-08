from flask import render_template, request, session, redirect, Blueprint, url_for
import flask_paginate
from bson.objectid import ObjectId
from utils import db_handler
from utils.db_connector import db_connection
from utils.logger import logger
from utils import config

event_logger = logger()

action_details = Blueprint("custom_action", __name__)

rows_per_page = 5


@action_details.route("/custom_action")
def custom_action():
    return render_template("admin/action_form.html")


@action_details.route("/action_list")
def action_list():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    try:
        session["status"] = "action"
        all_actions = db_handler.fetch_all_actions()
        _all_actions = []
        for idx, x in enumerate(all_actions):
            id = ObjectId(x.get("_id"))
            _all_actions.append([idx + 1, x.get("action_name"), x.get("url"), id])
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")
    page = request.args.get(flask_paginate.get_page_parameter(), type=int, default=1)
    offset = (page - 1) * rows_per_page
    x = (int(page) - 1) * rows_per_page
    y = int(page) * rows_per_page
    data = _all_actions[x:y]
    pagination = flask_paginate.Pagination(
        page=page,
        per_page=rows_per_page,
        offset=offset,
        total=len(_all_actions),
        record_name="_all_stories",
        css_framework="bootstrap5",
    )

    return render_template("admin/action_list.html", data=data, pagination=pagination)


@action_details.route("/form_action", methods=["POST"])
def form_action():
    """
    Add Single Action and redirect to Add Form
    :return: Redirect to Add Form View
    """

    projectpath = request.form
    x = db_handler.insert_action_form(projectpath)
    return render_template("admin/500.html")


@action_details.route("/delete_action", methods=["POST"])
def delete_action():
    """
    Delete Action Data and Redirect to Action List
    :return: Redirect to Action List View
    """
    try:
        projectpath = request.form
        db_handler.delete_single_action(projectpath)
        return redirect(
            url_for("custom_action.action_list", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@action_details.route("/replace")
def edit_action():
    """
    Edit Action details
    :id: Action Object Id
    :return: Action View with
        data: Action Details
        x_data: Action Example List
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
        my_collection = db_connection["action_form"]
        all_db_actions = my_collection.find({"_id": ObjectId(id_)})

        all_actions = []
        for x in all_db_actions:
            all_actions.append(x["token"])
            all_actions.append(x["action_name"])
            all_actions.append(x["token_value"])
            all_actions.append(x["url"])
            all_actions.append(x["method_type"])
            all_actions.append(x["request_type"])
            all_actions.append(x["request_body"])
            all_actions.append(x["response_body"])
            all_actions.append(id_)

        return render_template(
            "admin/edit_action.html",
            data=all_actions,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@action_details.route("/update_action", methods=["POST"])
def update_action():
    """
    Update Action Data and Redirect to Action List
    :return: Redirect to Action List View
    """
    try:
        projectpath = request.form
        db_handler.update_single_action(projectpath)

        return redirect(
            url_for("custom_action.action_list", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")
