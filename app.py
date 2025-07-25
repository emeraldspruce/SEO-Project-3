from flask import Flask, render_template, abort, request, session, redirect, url_for
from dotenv import load_dotenv
from database import Database 
import os
import subprocess
import sys
from geminiCardOutput import get_recommended_card

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = None

def init_app():
    '''Runs once at the start to initialize the app with any necessary configurations.'''
    db = Database()

init_app()

@app.route("/")
def first_page():
    return render_template("first_page.html")

@app.route("/second_page")
def second_page():
    global db
    if db is None:
        db = Database()

    id = session.get('user_id')
    if id is not None:
        db.add_user_card(user_id=id, card_id=db.get_card_id_by_name("Blue Business Cash"))
        db.add_user_card(user_id=id, card_id=db.get_card_id_by_name("Blue Business Plus"))
    return render_template("second_page.html")

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