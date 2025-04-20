from flask import Flask, redirect, url_for, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
import datetime as py_datetime
import time, threading
import os
from dotenv import load_dotenv

load_dotenv()

IP_address = os.getenv("IP_ADDRESS")
Port = os.getenv("PORT")
Debug_mode = os.getenv("DEBUG")

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Streak(db.Model):
    day = db.Column("day", db.Integer, primary_key = True)
    date = db.Column("date", db.Date)
    status = db.Column("Nofap_status", db.Boolean)
    streak_days = db.Column("Days_without_fapping", db.Integer)
    attempt_number = db.Column("Attempt_number", db.Integer)
    streak_started = db.Column("New_streak_attempt_started", db.Boolean)

    def __init__(self, day: int, date: py_datetime.datetime, status: bool, streak_days = None, attempt_number = None, streak_started = None):
        self.day = day
        self.date = date
        self.status = status
        self.streak_days = streak_days
        self.attempt_number = attempt_number
        self.streak_started = streak_started

class Record(db.Model):
    id = db.Column("id", db.Integer, primary_key = True)
    days = db.Column("days", db.Integer)

    def __init__(self, days: int):
        self.days = days

@app.route("/", methods = ["POST", "GET"])
def home():
    today = Streak.query.filter_by(date = py_datetime.datetime.today().date()).first()
    if request.method == "POST":
        match request.form["streakstatus"]:
            case "Start":
                today.streak_started = True
                db.session.commit()
            case "End":
                today.status = False
                today.streak_days = None
                today.attempt_number = None
                today.streak_started = False
                db.session.commit()

    #desc = str(today.day) + " " + str(today.date) + " " + str(today.status) + " " + str(today.streak_days) + " " + str(today.attempt_number) + " " + str(today.streak_started)
    return render_template("index.html", streak = today.streak_days, status = today.status, started = today.streak_started, record = Record.query.first().days)

@app.route("/history")
def history():
    streaks = Streak.query.all()
    return render_template("table.html", list = streaks, record = Record.query.first().days)

@app.route("/test")
def test():
    #abort(403)
    return str(request.remote_addr)

def update_database():
    with app.app_context():
        yesterday = Streak.query.order_by(Streak.day.desc()).first()
        if (yesterday == None):
            today = Streak(1, py_datetime.datetime.today().date(), status = False, streak_started = False)
            db.session.add(today)
            record = Record(0)
            db.session.add(record)
            db.session.commit()
            return
        if (yesterday.status):
            yesterday.streak_days += 1
            db.session.commit()
            today = Streak(yesterday.day + 1, py_datetime.datetime.today().date(), True, yesterday.streak_days, yesterday.attempt_number, True)
        else:
            if (yesterday.streak_started):
                today = Streak(yesterday.day + 1, py_datetime.datetime.today().date(), True, 0, Streak.query.order_by(Streak.attempt_number.desc()).first().attempt_number + 1, True)
            else:
                today = Streak(yesterday.day + 1, py_datetime.datetime.today().date(), False, streak_started = False)
        record = Record.query.first()
        if today.streak_days > record.days:
            record.days = today.streak_days
        db.session.add(today)
        db.session.commit()

def date_checker_thread():
    global today_date
    while True:
        if (today_date != str(py_datetime.datetime.today().date())):
            today_date = str(py_datetime.datetime.today().date())
            update_database()
        time.sleep(0.1)

date_checker = threading.Thread(target=date_checker_thread)
date_checker.daemon = True # This will make the thread exit when the main program exits
today_date = ""

if __name__ =="__main__":
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not Debug_mode:
        with app.app_context():
            db.create_all()
            today = Streak.query.order_by(Streak.day.desc()).first()
            if today == None:
                today_date = str(py_datetime.datetime.today().date())
                update_database()
            else:
                today_date = str(today.date)
        if not date_checker.is_alive():
            date_checker.start()
    app.run(debug=Debug_mode, host = IP_address, port = Port)