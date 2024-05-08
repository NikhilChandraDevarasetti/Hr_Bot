from flask import render_template, request, session, redirect, Blueprint, Response, url_for
from utils.logger import logger
from controller import docs_to_json
from utils.db_connector import db_connection
from whoosh.index import create_in
from whoosh.fields import *
import os

event_logger = logger()

document_details = Blueprint("document", __name__)


@document_details.route("/add_document")
def add_document():
    """
    Admin Dashboard
    :return: Admin DashBoard View
    """

    session["status"] = "document"
    return render_template("admin/doc_upload.html")


@document_details.route("/validate_document", methods=["POST"])
def validate_document():
    """
    Add document and redirect to Add Document
    :return: Redirect to Add Document View
    """
    try:

        if not os.path.exists("index"):
            os.mkdir("index")

        schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
        ix = create_in("index", schema)


        uploaded_file = request.files['upload_document']
        file_to_read = uploaded_file.read()

        description = request.form['description']
        original_doc = docs_to_json.Docx2Json()
        data = original_doc.process(file_to_read, uploaded_file.filename.split('.')[0])

        for i in range(len(data)):
            data[i]['Description'] = description

            writer = ix.writer()
            writer.add_document(title=data[i]['text'])
            writer.commit()

        return redirect(url_for('document.add_document', _external=True))
    except Exception as e:
        print(str(e))
        event_logger.error(e)
        return render_template("admin/500.html")






