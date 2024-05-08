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
from datetime import datetime
import random
import requests
import json

sso_auth = Blueprint("sso", __name__)
from utils.logger import logger
from utils import config
event_logger = logger()


@sso_auth.route("/ssologin")
def ssologin():
    """
    User Login using sso
    :return: Login Page View
    """
    try:
        if request.args.get("token"):
            token = request.args.get("token")
            event_logger.info(token)
            arr = {
                "token": token,
                "ip": "114.143.208.34",
            }
            api_params = {"form_params": arr}
            api_url = "https://sso.neosofttech.com/sso/verify-token-validity"
            result = requests.post(url=api_url, json=arr)
            # result = True
            user_data = result.json()
            event_logger.info(user_data)
            if result:
                email = user_data["email_id"]
                my_collection = db_connection["admin_login"]
                role_collection = db_connection["admin_role"]
                checkuser = my_collection.count_documents({"email": email})
                if checkuser == 0:
                    ct = datetime.now()
                    ts = ct.timestamp()
                    nlu_time = int(ts)
                    ran = random.randint(10, 40)
                    admin_id = str(nlu_time) + str(ran)
                    mydict = {
                        "name": email,
                        "username": email,
                        "password": "password",
                        "role": "4",
                        "email": email,
                        "status": "1",
                        "admin_id": str(admin_id),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    _id = my_collection.insert_one(mydict)


                user = my_collection.find({"email": email})
                user_details = []
                for x in user:
                    user_details.append(x["email"])
                    user_details.append(x["role"])
                    user_details.append(x["admin_id"])
                    user_details.append(x["username"])
                session["islogin"] = 1
                session["username"] = user_details[3]
                session["admin_id"] = user_details[2]
                session["role"] = user_details[1]
                all_access = role_collection.find(
                    {"role_id": user_details[1]}, {"access": 1}
                )
                x_data = []
                if user_details[1] == "1":
                    return redirect(
                        url_for("admin.dashboard", _external=True, _scheme=config.SSL_SECURITY)
                    )
                for id, y in enumerate(all_access):
                    x_data.append(y["access"])
                session["access"] = x_data[0]

                if user_details[1] == "1":
                    return redirect(
                        url_for("admin.dashboard", _external=True, _scheme=config.SSL_SECURITY)
                    )
                elif user_details[1] == "2":
                    return redirect(
                        url_for(
                            "admin.author_dashboard", _external=True, _scheme=config.SSL_SECURITY
                        )
                    )
                elif user_details[1] == "3":
                    return redirect(
                        url_for(
                            "admin.approver_dashboard", _external=True, _scheme=config.SSL_SECURITY
                        )
                    )
                else:
                    return render_template("admin/mobile_view.html", user_id=session["admin_id"])
                    # return render_template("admin/res_bot.html", user_id=session["admin_id"])
                    # return redirect(url_for("admin.user_chat", _external=True, _scheme=config.SSL_SECURITY))
            else:
                return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
        else:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/502.html")
