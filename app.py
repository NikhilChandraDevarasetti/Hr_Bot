from datetime import datetime
from random import random

from flask import Flask, render_template, request, session, redirect, Response, url_for,flash
from flask_session import Session
from flask_session_captcha import FlaskSessionCaptcha


from utils.db_connector import db_connection
from utils import config

from controller.intent import intent_details
from controller.auth import admin_auth
from controller.training import training_details
from controller.admin import admin_details
from controller.chatbot import chatbot_details
from controller.response import response_details
from controller.story import story_details
from controller.custom_action import action_details
from controller.sso_login import sso_auth

from utils.logger import logger
import requests
import json
import os
import redis
from controller.document import document_details
from whoosh.qparser import QueryParser
from whoosh.qparser import OrGroup
from whoosh import scoring
from whoosh.index import open_dir



app = Flask(__name__)
app.register_blueprint(intent_details)
app.register_blueprint(admin_auth)
app.register_blueprint(training_details)
app.register_blueprint(admin_details)
app.register_blueprint(chatbot_details)
app.register_blueprint(response_details)
app.register_blueprint(story_details)
app.register_blueprint(action_details)
app.register_blueprint(sso_auth)
app.register_blueprint(document_details)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "/static/")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = config.SESSION_TYPE
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = 6
app.config['CAPTCHA_WIDTH'] = 1500
app.config['CAPTCHA_HEIGHT'] = 120
app.secret_key = config.SECRET_KEY
app.config["SSL_SECURITY"] = config.SSL_SECURITY



server_session = Session(app)
captcha = FlaskSessionCaptcha(app)


@app.route("/")
def dashboard():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """
    if session.get("islogin") != 1:
        return redirect(url_for('auth.login',_external=True,_scheme=config.SSL_SECURITY))
    session["status"] = "dashboard"
    if session.get("role") == "1":
        return redirect(url_for('admin.dashboard', _external=True, _scheme=config.SSL_SECURITY))
    elif session.get("role") == "2":
        return redirect(url_for('admin.author_dashboard', _external=True, _scheme=config.SSL_SECURITY))
    elif session.get("role") == "3":
        return redirect(url_for('admin.approver_dashboard', _external=True, _scheme=config.SSL_SECURITY))
    else:
        session["status"] = "testing"
        return redirect(url_for('testing', _external=True, _scheme=config.SSL_SECURITY))


@app.route("/testing")
def testing():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """

    return render_template(
        "admin/testing_new.html",
        prod_socket_uri=config.PROD_SOCKET_URI,
        prod_socket_path=config.PROD_SOCKET_PATH,
    )


@app.route("/prod_testing")
def prod_testing():
    """
    Production Environment for testing
    :return: Production Environment View
    """

    return render_template(
        "frontend/production.html",
        prod_socket_uri=config.PROD_SOCKET_URI,
        prod_socket_path=config.PROD_SOCKET_PATH,
    )


@app.route("/staging_testing")
def staging_testing():
    """
    Staging Environment for testing
    :return: Staging Environment View
    """

    return render_template(
        "frontend/staging.html",
        staging_socket_uri=config.STAGING_SOCKET_URI,
        staging_socket_path=config.STAGING_SOCKET_PATH,
    )


@app.route("/single_bot")
def single_bot():
    return render_template("admin/single_bot.html")


@app.route("/bot")
def bot():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """

    return render_template("chatbot/custom_bot.html")



@app.route("/bot_msg", methods=["POST"])
def bot_msg():
    my_collection = db_connection["conversations"]
    smart_doc_data = db_connection["documents_data"]

    message_url = "http://127.0.0.1:6002/webhooks/rest/webhook"
    headers = {"Content-type": "application/json"}
    projectpath = request.form
    query_data = projectpath.to_dict(flat=False)
    msg = query_data.pop("msg")[0]
    print(msg,'msg is *************************************************************************************************')
    type = query_data.pop("type")[0]
    user_id = '16730026842' #session["admin_id"]
    # user_id = query_data.pop("user_id")[0] #session["admin_id"]
    payload_old = '{"sender": "' + user_id + '", "message": "' + msg + '"}'
    r = requests.post(message_url, data=payload_old.encode("utf-8"), headers=headers)
    response = json.loads(r.content)
    print(response, 'response is *******************************************************************************************')
    print(len(response))
    try:
 
        #if response[0]['text'] == "I didn't understand you. Please select options mentioned below.":
        if len(response)=='' or response[0]['text'] == "I didn't understand you. Please select options mentioned below.":
            ix = open_dir("index")
            qp = QueryParser("title", schema=ix.schema, group=OrGroup)
            q = qp.parse(msg)
            with ix.searcher(weighting=scoring.TF_IDF()) as s:
                results = s.search(q, terms=True)
                doc_response = [{'recipient_id': 'default', 'text':results[0]['title'] }]
                return render_template("chatbot/chats.html", bot_response=doc_response)


    except :
        doc_response = [{"recipient_id": "default", "text": "I didn't understand you. Please select options mentioned below."}]
        return render_template("chatbot/chats.html", bot_response=doc_response)	
        
    return render_template("chatbot/chats.html", bot_response=response, type=type)

	
   

@app.route("/user_login", methods=["POST"])
def user_login():
    projectpath = request.form
    query_data = projectpath.to_dict(flat=False)
    email = query_data.pop("email")[0]
    my_collection = db_connection["admin_login"]
    role_collection = db_connection["admin_role"]
    checkuser = my_collection.find({"email": email}).count()
    if checkuser > 0:
        return "1"
    else:
        return "0"

@app.route("/admin_login", methods=["POST"])
def admin_login():
    """
    Check User Authentication
    :return: Redirect Dashboard View
    """
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        username = query_data.pop("username")[0]
        print(username,'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        password = query_data.pop("password")[0]
        my_collection = db_connection["admin_login"]
        role_collection = db_connection["admin_role"]
        checkuser = my_collection.count_documents(
            {"username": username, "password": password})
        print(checkuser,'################################################################')
        if captcha.validate():
            if checkuser > 0:
                session.permanent = False
                user = my_collection.find({"username": username, "password": password})
                user_details = []
                for x in user:
                    user_details.append(x["email"])
                    user_details.append(x["role"])
                    user_details.append(x["admin_id"])
                    user_details.append(x["name"])
                session["islogin"] = 1
                session["name"] = user_details[3]
                session["username"] = username
                session["admin_id"] = user_details[2]
                session["role"] = user_details[1]
                all_access = role_collection.find(
                    {"role_id": user_details[1]}, {"access": 1}
                )
                x_data = []
                if user_details[1] == "1":
                    print('&&&&&&&&&&&&&&&&&&&&&&&&')
                    return redirect(
                        url_for("admin.dashboard", _external=True, _scheme=config.SSL_SECURITY)
                    )
                for id, y in enumerate(all_access):
                    x_data.append(y["access"])
                session["access"] = x_data[0]

                if user_details[1] == "1":
                    print('########################################')   
                    return redirect(
                        url_for("admin.dashboard", _external=True, _scheme=config.SSL_SECURITY)
                    )
                elif user_details[1] == "2":
                    print('$$$$$$$$$$$$$$$$$$') 
                    return redirect(
                        url_for("admin.author_dashboard", _external=True, _scheme=config.SSL_SECURITY)
                    )
                elif user_details[1] == "3":
                    print('#######################') 
                    return redirect(
                        url_for("admin.approver_dashboard", _external=True, _scheme=config.SSL_SECURITY)
                    )
                else:
                    return redirect(url_for('testing', _external=True, _scheme=config.SSL_SECURITY))
            else:
                flash(message='Invalid Username or Password')
                return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
        else:
            flash(message='Invalid Captcha')
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))

    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")




@app.route("/dummy")
def dummy():
    my_collection = db_connection["nlu_data"]
    x = my_collection.find({"intent": "greet"}, {"title": 1})
    nlu_data = ""
    for nlu_ids in x:
        nlu_data = nlu_ids["title"]
    return nlu_data


if __name__ == "__main__":
    event_logger = logger()
    event_logger.info("Loading bot app.")
    app.run('0.0.0.0',port='6001',debug=True)
