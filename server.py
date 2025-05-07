from flask import Flask, redirect, url_for, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime as py_datetime
import time, threading
import os
import sys
import enum
from dotenv import load_dotenv

load_dotenv()

IP_address = os.getenv("IP_ADDRESS")
Port = os.getenv("PORT")
Debug_mode = os.getenv("DEBUG")

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Mode(enum.Enum):
    Normal = 1
    Hard = 2

class Streak(db.Model):
    day = db.Column("day", db.Integer, primary_key = True)
    date = db.Column("date", db.Date)
    status = db.Column("Nofap_status", db.Boolean)
    streak_days = db.Column("Days_without_fapping", db.Integer)
    attempt_number = db.Column("Attempt_number", db.Integer)
    streak_started = db.Column("New_streak_attempt_started", db.Boolean)
    mode = db.Column("Mode", db.Enum(Mode))

    def __init__(self, day: int, date: py_datetime.datetime, status: bool, streak_days = None, attempt_number = None, streak_started = None, mode = Mode.Normal):
        self.day = day
        self.date = date
        self.status = status
        self.streak_days = streak_days
        self.attempt_number = attempt_number
        self.streak_started = streak_started
        self.mode = mode

class Record(db.Model):
    id = db.Column("id", db.Integer, primary_key = True)
    days = db.Column("days", db.Integer)
    day = db.Column("day", db.Date)

    def __init__(self, days: int, day: py_datetime.datetime):
        self.days = days

@app.route("/", methods = ["POST", "GET"])
def home():
    today = Streak.query.filter_by(date = py_datetime.datetime.today().date()).first()
    if request.method == "POST":
        match request.form["streakstatus"]:
            case "Start":
                today.streak_started = True
                match request.form["mode"]:
                    case "Normal":
                        today.mode = Mode.Normal
                    case "Hard":
                        today.mode = Mode.Hard
                db.session.commit()
            case "End":
                today.status = False
                today.streak_days = None
                today.attempt_number = None
                today.streak_started = False
                today.mode = None
                db.session.commit()

    #desc = str(today.day) + " " + str(today.date) + " " + str(today.status) + " " + str(today.streak_days) + " " + str(today.attempt_number) + " " + str(today.streak_started)
    if today.mode != None:
        t_mode = today.mode.name
    else:
        t_mode = ""
    s_record = Record.query.order_by(Record.days.desc()).first().days
    return render_template("index.html", streak = today.streak_days, status = today.status, started = today.streak_started, record = s_record, mode = t_mode, today = str(py_datetime.datetime.today().date()))

@app.route("/history")
def history():
    streaks = Streak.query.all()
    s_record = Record.query.order_by(Record.days.desc()).first().days
    return render_template("table.html", list = streaks, record = s_record)

@app.route("/test")
def test():
    #abort(403)
    return str(request.remote_addr)

@app.route("/records")
def records():
    records = Record.query.all()
    return render_template("records.html", list = records)

def update_database():
    with app.app_context():
        yesterday = Streak.query.order_by(Streak.day.desc()).first()
        # check if db is empty
        if (yesterday == None):
            today = Streak(1, py_datetime.datetime.today().date(), status = False, streak_started = False)
            db.session.add(today)
            record = Record(0)
            db.session.add(record)
            db.session.commit()
            return
        streak_days = None
        attempt_number = None
        day = yesterday.day + 1
        date = py_datetime.datetime.today().date()
        # status
        if (yesterday.status):
            yesterday.streak_days += 1
            db.session.commit()
            status = True
        else:
            if (yesterday.streak_started):
                status = True
            else:
                status = False
        # streak_days
        if status:
            if yesterday.status:
                streak_days = yesterday.streak_days
            else:
                streak_days = 0
        # attempt_number
        previous_attempt = Streak.query.order_by(Streak.attempt_number.desc()).first().attempt_number
        if previous_attempt == None:
            previous_attempt = 0
        if status:
            if not yesterday.status:
                attempt_number = previous_attempt + 1
            else:
                attempt_number = previous_attempt
        # streak_started
        streak_started = yesterday.streak_started
        # mode
        mode = yesterday.mode

        today = Streak(day, date, status, streak_days, attempt_number, streak_started, mode)
        db.session.add(today)
        
        record = Record.query.order_by(Record.days.desc()).first().days
        if today.streak_days > record:
            newrecord = Record(today.streak_days, today.date)
            db.session.add(newrecord)

        db.session.commit()

def date_checker_thread(today_date: str):
    while True:
        if (today_date != str(py_datetime.datetime.today().date())):
            today_date = str(py_datetime.datetime.today().date())
            update_database()
        time.sleep(0.1)

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
        date_checker = threading.Thread(target=date_checker_thread, args=(today_date, ))
        date_checker.daemon = True # This will make the thread exit when the main program exits
        if not date_checker.is_alive():
            date_checker.start()
    app.run(debug=Debug_mode, host = IP_address, port = Port)