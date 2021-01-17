from flask import Flask, render_template, redirect, request, flash, session, url_for, make_response
from flask_session import Session
from bcrypt import hashpw, checkpw, gensalt
from dotenv import load_dotenv
from redis import StrictRedis
from os import getenv
from re import match
from datetime import datetime
from uuid import uuid4
from jwt import encode

from six.moves.urllib.parse import urlencode
from authlib.integrations.flask_client import OAuth

import datetime as dt
import requests
import json

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

load_dotenv()

AUTH0_CALLBACK_URL = getenv("AUTH0_CALLBACK_URL")
AUTH0_CLIENT_ID = getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = getenv("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = getenv("AUTH0_DOMAIN")
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = getenv("AUTH0_AUDIENCE")
SOCKET_URL = getenv("SOCKET_URL")

WS_URL = getenv("WS_URL")
JWT_SECRET = getenv("JWT_SECRET")
REDIS_HOST = getenv("REDIS_HOST")
REDIS_PASS = getenv("REDIS_PASS")
db = StrictRedis(host=REDIS_HOST, port=6379, db=13, password=REDIS_PASS)

SESSION_TYPE = "redis"
SESSION_REDIS = db
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = getenv("SECRET_KEY")
ses = Session(app)

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=AUTH0_BASE_URL,
    access_token_url=AUTH0_BASE_URL + '/oauth/token',
    authorize_url=AUTH0_BASE_URL + '/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)

def getCurrentUserLabels():
    if not isLogged():
        return None
    username = session["logged-as"]

    payload = {
        "usertype" : "Sender",
        "username" : username,
        "exp" : datetime.now() + dt.timedelta(seconds=15)
    }

    token = encode(payload=payload, key=JWT_SECRET, algorithm='HS256')
    headers = {"Authorization" : "Bearer " + token }

    res = requests.get(WS_URL, headers= headers)

    try:
        next_link = WS_URL + res.json()["_links"]["labels"]["href"]
    except Exception:
        flash("Usługa jest obecnie niedostępna, spróbuj ponownie później")
        return None

    res = requests.get(next_link, headers= headers)

    try:
        labels = res.json()["items"]
    except Exception:
        flash("Usługa jest obecnie niedostępna, spróbuj ponownie później")
        return None

    return labels

def isDatabase():
    database = db
    return database.ping() if database else None

def isLogged():
    return "logged-as" in session

def isUser(username):
    return db.hexists(f"username:{username}", "password")

def addLabel(person, size, destination):
    username = session["logged-as"]

    payload = {
        "usertype" : "Sender",
        "username" : username,
        "exp" : datetime.now() + dt.timedelta(seconds=15)
    }

    token = encode(payload=payload, key=JWT_SECRET, algorithm='HS256')
    headers = {"Authorization" : "Bearer " + token}

    res = requests.get(WS_URL, headers= headers)

    try:
        next_link = WS_URL + res.json()["_links"]["labels"]["href"]
    except Exception:
        flash("Nie można dodać etykiety, ponieważ usługa sieciowa jest niedostępna, spróbuj ponownie później")
        return

    label = {
        "person" : person,
        "size" : size,
        "destination" : destination
    }

    res = requests.post(next_link, headers= headers, json= label)
    if res.status_code != 200:
        flash("Nie można dodać etykiety, ponieważ usługa sieciowa jest niedostępna, spróbuj ponownie później")

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

def deleteLabel(label):
    username = session["logged-as"]
    payload = {
        "usertype" : "Sender",
        "username" : username,
        "exp" : datetime.now() + dt.timedelta(seconds=15)
    }

    token = encode(payload=payload, key=JWT_SECRET, algorithm='HS256')
    headers = {"Authorization" : "Bearer " + token}

    res = requests.get(WS_URL, headers= headers)

    try:
        next_link = WS_URL + res.json()["_links"]["labels"]["href"]
    except Exception:
        flash("Nie można usunąć etykiety, ponieważ usługa sieciowa jest niedostępna, spróbuj ponownie później")
        return

    res = requests.get(next_link, headers= headers)

    try:
        next_link = WS_URL + res.json()["_links"]["label:info"]["href"]
    except Exception:
        flash("Nie można usunąć etykiety, ponieważ usługa sieciowa jest niedostępna, spróbuj ponownie później")
        return
    
    next_link = next_link.format(id= label)
    res = requests.get(next_link, headers= headers)

    try:
        links = res.json()["_links"]
    except Exception:
        flash("Nie można usunąć etykiety, ponieważ usługa sieciowa jest niedostępna, spróbuj ponownie później")
        return

    try:
        delete_link = WS_URL + links["label:delete"]["href"]
    except Exception:
        flash("Nie da się usunąć wybranej etykiety, ponieważ kurier odebrał już przesyłkę")
        return

    res = requests.delete(delete_link, headers= headers)

    if res.status_code != 204:
        flash("Nastąpił błąd w trakcie usuwania etykiety, skontaktuj się z administratorem lub spróbuj ponownie później")
    else:
        flash("Etykieta została usunięta")

def generate_socketio_token():
    if not "logged-as" in session:
        return ""
    username = session["logged-as"]
    payload = {
        "type" : "socketiotoken",
        "username" : username,
        "iat" : datetime.now(),
        "exp" : datetime.now() + dt.timedelta(minutes=120)
    }
    return encode(payload=payload, key=JWT_SECRET, algorithm='HS256')

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
    session["display-name"] = username
    session["logged-at"] = str(datetime.now())

    return redirect("/sender/dashboard", code=301)

# dashboard -------------------
@app.route("/sender/dashboard", methods=["GET"])
def dashboardForm():
    if not isLogged():
        return redirect("/sender/login", code=301)
    if not isDatabase():
        flash("Błąd połączenia z bazą danych, skontaktuj się z Administratorem lub spróbuj później")
        return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=None, token="", socket_url="")

    return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=getCurrentUserLabels, token=generate_socketio_token(), socket_url=SOCKET_URL)

@app.route("/sender/dashboard", methods=["POST"])
def dashboard():
    if not isLogged():
        return redirect("/sender/login", code=301)
    
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
        return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=getCurrentUserLabels, token=generate_socketio_token(), socket_url=SOCKET_URL)

    addLabel(person, size, destination)

    return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=getCurrentUserLabels, token=generate_socketio_token(), socket_url=SOCKET_URL)


# logout    -------------------
@app.route("/sender/logout")
def logout():
    if "login-type" in session:
        if session["login-type"] == "auth0":
            session.clear()
            params = {'returnTo': url_for('index', _external=True), 'client_id': AUTH0_CLIENT_ID}
            return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))
    else:
        session.clear()
        return redirect("/", code=301)

# removelabel
@app.route("/sender/dashboard/removelabel/", methods=["POST"])
def removelabel():
    if not isLogged():
        return redirect("/sender/login", code=301)
    
    label = request.form.get("label")

    if not isDatabase():
        flash("Błąd połączenia z bazą danych, skontaktuj się z Administratorem lub spróbuj później")
        return render_template("dashboard.html", packageSizes=_packageSizes, packageDestinations=_packageDestinations, getCurrentUserLabels=None, token="", socket_url="")

    if not label:
        flash("Błąd w trakcie usuwania etykiety")
        return redirect("/sender/dashboard", code=301)
    
    deleteLabel(label)

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


# auth0
@app.route('/auth0/login')
def auth0_login():
    return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL, audience=AUTH0_AUDIENCE)

@app.route('/callback')
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    if not db.keys(userinfo["sub"]):
        db.set(userinfo["sub"], "")

    session["logged-as"] = userinfo["sub"]
    session["display-name"] = userinfo["name"]
    session["login-type"] = "auth0"

    return redirect('/sender/dashboard')

if __name__ == "__main__":
    app.run()