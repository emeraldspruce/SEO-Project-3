from flask import Flask, render_template, abort, request, session, redirect, url_for, flash
from dotenv import load_dotenv
from werkzeug.utils import secure_filename 
import uuid
import os
import subprocess
import sys
from geminiCardOutput import get_recommended_card


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def init_app():
    '''Runs once at the start to initialize the app with any necessary configurations.'''

init_app()
@app.errorhandler(404)
def page_not_found(e):
    '''Handles 404 errors by rendering a custom 404 page.'''
    return render_template("404.html"), 404

@app.route("/")
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/first_page")
def first_page():
    return render_template("first_page.html")

@app.route("/second_page", methods=["GET", "POST"])
def second_page():
    return render_template("second_page.html")

UPLOAD_FOLDER = 'uploads'  
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/upload_statement", methods=["POST"])
def upload_statement():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(url_for('second_page'))

    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(url_for('second_page'))

    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename) 
        unique_filename = f"{uuid.uuid4().hex}_{filename}"  
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        flash("File uploaded successfully!")
        return redirect(url_for('second_page'))
    else:
        flash("Invalid file type. Please upload a CSV file.")
        return redirect(url_for('second_page'))

@app.route("/third_page")
def third_page():
    return render_template("third_page.html")

@app.route("/gemini_rec", methods=["GET", "POST"])
def gemini_rec():
    if request.method == "POST":
        description = request.form.get("description")
        if description:
            output = get_recommended_card(description)
            return render_template("gemini_rec.html", message=output)
    return render_template("gemini_rec.html")


if __name__ == "__main__":
    app.run(debug=True)