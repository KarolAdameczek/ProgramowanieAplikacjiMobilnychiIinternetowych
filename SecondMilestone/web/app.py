from flask import Flask, render_template, redirect, request, flash, session, url_for, make_response
from flask_session import Session
from bcrypt import hashpw, checkpw, gensalt
from dotenv import load_dotenv
from redis import StrictRedis
from os import getenv
from re import match
from datetime import datetime
from uuid import uuid4

_regex = {
    "firstname": r"[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+",
    "lastname":  r"[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+",
    "username":  r"^[a-z]{3,12}$",
    "password":  r"^.{8,}$",
    "address":   r"^[A-ZŻŹĆĄŚĘŁÓŃa-zżźćńółęąś. 0-9]{8,100}$",
    "email":     r"^(([^<>()\[\]\.,;:\s@\"]+(\.[^<>()\[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$",
    "person":    r"[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+ [A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+"
}

_onIncorrectRegisterMessgae = {
    "firstname": "Niepoprawne imię",
    "lastname":  "Niepoprawne nazwisko",
    "username":  "Niepoprawna nazwa użytkownika",
    "password":  "Niepoprawne hasło",
    "address":   "Niepoprawny adres",
    "email":     "Niepoprawny email"
}

_packageSizes = {
    "small"  : "Mała",
    "medium" : "Średnia",
    "large"  : "Duża"
}

_packageDestinations = {
    "WAW01" : "Warszawa",
    "KRA02" : "Kraków",
    "GDA03" : "Gdańsk"
}

REDIS_HOST = getenv("REDIS_HOST")
REDIS_PASS = getenv("REDIS_PASS")
db = StrictRedis(host=REDIS_HOST, port=6379, db=13, password=REDIS_PASS)

load_dotenv()
SESSION_TYPE = "redis"
SESSION_REDIS = db
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = getenv("SECRET_KEY")
ses = Session(app)

def getCurrentUserLabels():
    if not isLogged():
        return None
    username = session["logged-as"]
    labelKeys = db.keys(f"label:{username}:*")
    labels = []
    for key in labelKeys:
        fields = db.hgetall(key)
        labels.append({ k.decode() : fields[k].decode() for k in fields })

    return labels

def isDatabase():
    database = db
    return database.ping() if database else None

def isLogged():
    return "logged-as" in session

def isUser(username):
    return db.hexists(f"username:{username}", "password")

def addLabel(label, username, person, size, destination):
    db.hset(f"label:{username}:{label}", "person", person)
    db.hset(f"label:{username}:{label}", "size", size)
    db.hset(f"label:{username}:{label}", "label", label)
    db.hset(f"label:{username}:{label}", "destination", destination)

def addUser(username, password, address, email, firstname, lastname):
    salt = gensalt(8)
    hashed = hashpw(password.encode(), salt)
    db.hset(f"username:{username}", "password", hashed)
    db.hset(f"username:{username}", "address", address)
    db.hset(f"username:{username}", "email", email)
    db.hset(f"username:{username}", "firstname", firstname)
    db.hset(f"username:{username}", "lastname", lastname)

def checkUser(username, password):
    password = password.encode()
    hashed = db.hget(f"username:{username}", "password")
    if not hashed:
        return False
    return checkpw(password, hashed)

def deleteLabel(username, label):
    return db.delete(f"label:{username}:{label}")

# prevents caching
@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# passing values to base template
@app.context_processor
def passToTemplates():
    return {"userLogged" : isLogged, "session" : session}

# index     -------------------
@app.route("/")
def index():
    return render_template("index.html")

# register  -------------------
@app.route("/sender/register", methods=["GET"])
def registerForm():
    if isLogged():
        return redirect("/sender/dashboard", code=301)
    return render_template("register.html")

@app.route("/sender/register", methods=["POST"])
def register():
    if isLogged():
        return redirect("/sender/dashboard", code=301)
    data = {}
    data["firstname"] = request.form.get("firstname")
    data["lastname"]  = request.form.get("lastname")
    data["username"]  = request.form.get("username")
    data["password"]  = request.form.get("password")
    data["address"]   = request.form.get("address")
    data["email"]     = request.form.get("email")
    
    anyInvalid = False
    for key in data:
        if data[key] is None or not match(_regex[key], data[key]):
            flash(_onIncorrectRegisterMessgae[key])
            anyInvalid = True
    if anyInvalid:
        return render_template("register.html")

    if not isDatabase():
        flash("Błąd połączenia z bazą danych, skontaktuj się z Administratorem lub spróbuj później")
        return render_template("register.html")

    if isUser(data["username"]):
        flash("Istnieje już taka nazwa użytkownika")
        return render_template("register.html")
    
    addUser(data["username"], data["password"], data["address"], data["email"], data["firstname"], data["lastname"] )
    return redirect(url_for("loginForm"), code=301)

# login     -------------------
@app.route("/sender/login", methods=["GET"])
def loginForm():
    if isLogged():
        return redirect("/sender/dashboard", code=301)
    return render_template("login.html")

@app.route("/sender/login", methods=["POST"])
def login():
    if isLogged():
        return redirect("/sender/dashboard", code=301)

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Nie podano nazwy użytkownika lub hasła")
        return render_template("login.html") 

    if not isDatabase():
        flash("Błąd połączenia z bazą danych, skontaktuj się z Administratorem lub spróbuj później")
        return render_template("login.html")

    if not checkUser(username, password):
        flash("Niepoprawna nazwa użytkownika lub hasło")
        return render_template("login.html") 

    session["logged-as"] = username
    session["logged-at"] = str(datetime.now())

    return redirect("/sender/dashboard", code=301)

# dashboard -------------------
@app.route("/sender/dashboard", methods=["GET"])
def dashboardForm():
    if not isLogged():
        return redirect("/sender/login", code=301)
    if not isDatabase():
        flash("Błąd połączenia z bazą danych, skontaktuj się z Administratorem lub spróbuj później")
        return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=None)

    return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=getCurrentUserLabels)

@app.route("/sender/dashboard", methods=["POST"])
def dashboard():
    if not isLogged():
        return redirect("/sender/login", code=301)
    
    username = session["logged-as"]
    person = request.form.get("person")
    size = request.form.get("size")
    destination = request.form.get("destination")

    valid = True
    if not person or not match(_regex["person"], person):
        flash("Niepoprawny adresat")
        valid = False
        
    if not size or size not in _packageSizes:
        flash("Niepoprawny rozmiar")
        valid = False
        
    if not destination or destination not in _packageDestinations:
        flash("Niepoprawny paczkomat")
        valid = False

    if not valid:
        return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=getCurrentUserLabels)

    if not isDatabase():
        flash("Błąd połączenia z bazą danych, skontaktuj się z Administratorem lub spróbuj później")
        return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=None)

    label = str(uuid4())
    addLabel(label, username, person, size, destination)
    return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=getCurrentUserLabels)


# logout    -------------------
@app.route("/sender/logout")
def logout():
    session.clear()
    return redirect("/", code=301)

# removelabel
@app.route("/sender/dashboard/removelabel/", methods=["POST"])
def removelabel():
    if not isLogged():
        return redirect("/sender/login", code=301)
    
    label = request.form.get("label")
    username = session["logged-as"]

    if not isDatabase():
        flash("Błąd połączenia z bazą danych, skontaktuj się z Administratorem lub spróbuj później")
        return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=None)

    if not label or not deleteLabel(username, label):
        flash("Błąd w trakcie usuwania etykiety")

    return redirect("/sender/dashboard", code=301)

# checkusername ---------------
@app.route("/sender/checkusername/<username>")
def checkusername(username):
    if not isDatabase():
        return {username: "error-in-database"}
    if isUser(username):
        return {username: "taken"}
    else:
        return {username: "available"}


if __name__ == "__main__":
    app.run()