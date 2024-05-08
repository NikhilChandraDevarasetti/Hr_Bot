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
import json
from utils import config
from collections import OrderedDict


event_logger = logger()

story_details = Blueprint("story", __name__)

rows_per_page = 5


@story_details.route("/story")
def story():
    session["status"] = "story_list"
    nlu_data = db_connection["nlu_data"].find({"status": {"$ne": "7"}})  # nlu_data
    intents = [record["intent"] for record in nlu_data]

    response_list = list(create_dataset.fetch_temp_response().keys())
    return render_template("admin/story.html", intents=intents, responses=response_list)


@story_details.route("/display_stories")
def display_stories():
    """
    List of all Stories
    :return: Edit Story View with
        data: Story List(list)
        train: Count of Untrained Intents(string)
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    try:
        session["status"] = "story_list"
        all_stories = db_handler.fetch_all_stories()
        _all_stories = []
        for idx, x in enumerate(all_stories):
            id = ObjectId(x.get("_id"))
            _all_stories.append([idx + 1, x.get("steps"), x.get("story"), id])
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/404.html")

    page = request.args.get(flask_paginate.get_page_parameter(), type=int, default=1)
    offset = (page - 1) * rows_per_page
    x = (int(page) - 1) * rows_per_page
    y = int(page) * rows_per_page
    stories = _all_stories[x:y]
    pagination = flask_paginate.Pagination(
        page=page,
        per_page=rows_per_page,
        offset=offset,
        total=len(_all_stories),
        record_name="_all_stories",
        css_framework="bootstrap5",
    )

    return render_template("admin/story_list.html", data=stories, pagination=pagination)


@story_details.route("/create_story", methods=["POST"])
def create_story():
    projectpath = request.form
    query_data = dict(projectpath)
    steps_dict = []
    final_ = {}
    final_["story"] = query_data.pop("story_name")

    for one in query_data:
        if "intent" in one:
            steps_dict.append({"intent": query_data[one]})
        else:
            steps_dict.append({"action": query_data[one]})
    final_["steps"] = steps_dict

    db_connection["custom_stories"].insert_one(final_)
    return "Success"


@story_details.route("/delete_story", methods=["POST"])
def delete_story():
    """
    Delete Story Data and Redirect to Story List
    :return: Redirect to Story List View
    """
    try:
        projectpath = request.form
        db_handler.delete_single_story(projectpath)
        return redirect(
            url_for("story.display_stories", _external=True, _scheme=config.SSL_SECURITY)
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@story_details.route("/replace")
def edit_story():
    """
    Edit Story details
    :id: Story Object Id
    :return: Edit Story View with
        data: Story Details
        x_data: Story Example List
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
        session["status"] = "story"
        id_ = request.args.get("id")
        story_collection = db_connection["custom_stories"]
        story_to_edit = story_collection.find({"_id": ObjectId(id_)})
        all_stories = []
        intents = []

        nlu_data = db_connection["nlu_data"].find({"status": {"$ne": "7"}})
        intents = [record["intent"] for record in nlu_data]
        response_list = list(create_dataset.fetch_temp_response().keys())

        for x in story_to_edit:
            all_stories.append(x["steps"])
            all_stories.append(x["story"])
            all_stories.append(x["_id"])

        final_steps = []
        for one in all_stories[0]:
            if list(one.keys())[0] == "intent":
                final_steps.append(list(one.values())[0])
                intents.remove(list(one.values())[0])
            else:
                final_steps.append(list(one.values())[0])
                response_list.remove(list(one.values())[0])
        all_stories.append(final_steps)

        return render_template(
            "admin/edit_story.html",
            data=all_stories,
            intents=intents,
            responses=response_list,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@story_details.route("/update_story", methods=["POST"])
def update_story():
    """
    Update Story Data and Redirect to Story List
    :return: Redirect to Story List View
    """
    projectpath = request.form
    db_handler.update_single_story(projectpath)
    return "Success"
