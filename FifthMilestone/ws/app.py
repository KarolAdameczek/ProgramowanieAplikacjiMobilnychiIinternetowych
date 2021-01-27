from flask import Flask, request, g, make_response
from flask_hal import HAL
from flask_hal.link import Link
from flask_hal.document import Document
from redis import StrictRedis
from jwt import decode, InvalidTokenError, encode
from uuid import uuid4
from dotenv import load_dotenv
from os import getenv

import datetime
import json
import re

import invoicemaker
import logger

from courier_auth import courier_auth0_init, is_courier_authorized

_unauthorized = {"error" : "Unauthorized"}, 401

_package_sizes = [
    "small",
    "medium",
    "large"
]

_prices = {
    "small" : "8zł",
    "medium" : "10zł",
    "large" : "12zł"
}

_package_destinations = [
    "WAW01",
    "KRA02",
    "GDA03"
]

_package_statuses = [
    "moving",
    "delivered",
    "received"
]

load_dotenv()

REDIS_HOST = getenv("REDIS_HOST")
REDIS_PASS = getenv("REDIS_PASS")
JWT_SECRET = getenv("JWT_SECRET")
AUTH0_DOMAIN = getenv("AUTH0_DOMAIN")
API_IDENTIFIER = getenv("API_IDENTIFIER")
db = StrictRedis(host=REDIS_HOST, port=6379, db=13, password=REDIS_PASS, decode_responses=True)

app = Flask(__name__)
HAL(app)

courier_auth0_init(AUTH0_DOMAIN, API_IDENTIFIER)

def logUnauthorized():
    logger.log("Próba nieautoryzowanego dostępu do " + request.url, "ws.error")

def response_allowed_methods(methods: list):
    if "OPTIONS" not in methods:
        methods.append("OPTIONS")

    res = make_response("", 204)
    res.headers["Allow"] = ", ".join(methods)
    return res

def is_sender_authorized():
    check_sender_auth()
    if g.authorization != {} and g.authorization["usertype"] == "Sender":
        return True
    return False

def check_sender_auth():
    token = request.headers.get("Authorization", "").split()
    if len(token) != 2 or token[0] != "Bearer":
        g.authorization = {}
        return
    try:
        g.authorization = decode(token[1], JWT_SECRET, algorithms=["HS256"])
        if g.authorization["usertype"] != "Sender":
            g.authorization = {}
        if datetime.datetime.fromtimestamp(g.authorization["exp"]) < datetime.datetime.now():
            g.authorization = {}
    except InvalidTokenError:
        g.authorization = {}
    except KeyError:
        g.authorization = {}

@app.route("/", methods=["GET", "OPTIONS"])
def index():
    if not is_sender_authorized() and not is_courier_authorized():
        logUnauthorized()
        return _unauthorized

    if request.method == "OPTIONS":
        return response_allowed_methods(["GET"])

    links = []
    links.append(Link("labels", "/labels"))
    links.append(Link("packages", "/packages"))

    doc = Document(data={}, links=links).to_json()

    return doc

# PACKAGE 

# package template:
# package:id
# { "id" : id of coresponding label, 
#   "status" : _package_statuses }

@app.route("/packages", methods=["OPTIONS"])
def packages_options():
    if not is_courier_authorized():
        logUnauthorized()
        return _unauthorized
    return response_allowed_methods(["GET", "POST"])

@app.route("/packages", methods=["GET"])
def packages_get():
    if not is_courier_authorized():
        logUnauthorized()
        return _unauthorized
    package_keys = db.keys(f"package:*")
    packages = []
    for key in package_keys:
        packages.append(db.hgetall(key))

    links = []
    links.append(Link("package:info", "/packages/{id}"))
    doc = Document(data = {"items" : packages}, links=links).to_json()
    
    return doc

@app.route("/packages", methods=["POST"])
def packages_post():
    if not is_courier_authorized():
        logUnauthorized()
        return _unauthorized

    data = request.json

    if db.keys("package:" + data["id"]):
        return {"error" : "Taka paczka już istnieje"}, 400

    try:
        label = db.keys("label:*:" + data["id"])[0]
    except Exception:
        return {"error" : "Podano niepoprawne id"}, 400

    if not label:
        return {"error" : "Incorrect package id"}, 400

    db.hset(label, "state", "locked")

    try:
        match = re.match(r"^label:(.+):", label)
        username = match.group(1)
        message = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + " - Stworzono paczkę dla etykiety o id: " + data["id"]
        db.lpush("notifications:" + username, message)
        invoicemaker.sendInvoiceToQueue(data["id"], _prices[db.hget(label, "size")], username, db.hget(label, "person"))
    except Exception:
        print("Error while creating notification for creation of package with id: " + data["id"], flush=True)

    db.hmset("package:" + data["id"], {"id" : data["id"], "status" : _package_statuses[0]})

    package_keys = db.keys(f"package:*")
    packages = []
    for key in package_keys:
        packages.append(db.hgetall(key))
        
    links = []
    links.append(Link("package:info", "/packages/{id}"))
    doc = Document(data = {"items" : packages}, links=links).to_json()
    
    return doc

# PACKAGE by id

@app.route("/packages/<uid>", methods=["OPTIONS"])
def packages_id_options(uid):
    if not is_courier_authorized():
        logUnauthorized()
        return _unauthorized
    return response_allowed_methods(["GET, PUT"])

@app.route("/packages/<uid>", methods=["GET"])
def packages_id_get(uid):
    if not is_courier_authorized():
        logUnauthorized()
        return _unauthorized

    package = db.hgetall("package:" + uid)
    if not package:
        return {"error" : "No package found with this id"}, 400

    links = []
    links.append(Link("package:update", request.script_root + request.full_path))

    doc = Document(data={"item" : package}, links=links).to_json()

    return doc

@app.route("/packages/<uid>", methods=["PUT"])
def packages_id_put(uid):
    if not is_courier_authorized():
        logUnauthorized()
        return _unauthorized

    package = db.hgetall("package:" + uid)
    data = request.json

    if not package:
        return {"error" : "No package found with this id"}, 400
    if package["status"] == _package_statuses[-1]:
        return {"error" : "This package cannot be edited"}, 400

    db.hset("package:" + uid, "status", data["status"] )

    try:
        label_key = db.keys("label:*:" + uid)[0]
        match = re.match(r"^label:(.+):", label_key)
        username = match.group(1)
        message = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + " - Zmieniono status paczki " + uid + " na " + data["status"]
        db.lpush("notifications:" + username, message)
    except Exception:
        print("Error while creating notification for status update of package with id:" + uid, flush=True)

    links = []
    links.append(Link("package:update", request.script_root + request.full_path))
    doc = Document(data={"item" : package}, links=links).to_json()

    return doc

# LABEL 

# label template:
# label:username:id
# { "person" : "John Smith", 
#   "size" : "_package_sizes", 
#   "destination" : "_package_destinations"
#   "id" : uuid4(),
#   "state" : "created/locked" }

@app.route("/labels", methods=["OPTIONS"])
def labels_options():
    if is_courier_authorized() or is_sender_authorized():
        return response_allowed_methods(["GET", "POST"])
    else:
        logUnauthorized()
        return _unauthorized

@app.route("/labels", methods=["GET"])
def labels_get():
    if not is_sender_authorized() and not is_courier_authorized():
        logUnauthorized()
        return _unauthorized

    label_keys = []
    if is_sender_authorized() and g.authorization["username"]:
        label_keys = db.keys("label:" + g.authorization["username"] + ":*")
    elif is_courier_authorized():
        label_keys = db.keys("label:*")
    else:
        logUnauthorized()
        return _unauthorized

    labels = []
    for key in label_keys:
        labels.append(db.hgetall(key))

    links = []
    links.append(Link("label:info", "/labels/{id}"))

    doc = Document(data={"items": labels}, links=links).to_json()
    return doc

@app.route("/labels", methods=["POST"])
def labels_post():
    if not is_sender_authorized():
        logUnauthorized()
        return _unauthorized

    data = request.json
    if not data:
        return {"error" : "No JSON data provided"}, 400
    
    try:
        if data["person"] == "":
            return {"error" : "Wrong person value"}, 400
        if data["size"] not in _package_sizes:
            return {"error" : "Wrong size value"}, 400
        if data["destination"] not in _package_destinations:
            return {"error" : "Wrong destination value"}, 400
    except Exception:
        return {"Not enough data provided"}, 400

    newdata = {
        "person" : data["person"],
        "destination" : data["destination"],
        "size" : data["size"],
        "id" : str(uuid4()),
        "state" : "created"
    }

    username = g.authorization["username"]
    db.hmset("label:" + username + ":" + newdata["id"], newdata)

    label_keys = db.keys("label:" + username + ":*")
    labels = []
    for key in label_keys:
        labels.append(db.hgetall(key))

    links = []
    links.append(Link("label:info", "/labels/{id}"))

    doc = Document(data={"items": labels}, links=links).to_json()

    return doc

# LABEL by id

@app.route("/labels/<uid>", methods=["OPTIONS"])
def labels_id_options(uid):
    if not is_sender_authorized():
        logUnauthorized()
        return _unauthorized
    
    return response_allowed_methods(["GET", "DELETE"])

@app.route("/labels/<uid>", methods=["GET"])
def labels_id_get(uid):
    if not is_sender_authorized():
        logUnauthorized()
        return _unauthorized

    username = g.authorization["username"]

    label = db.hgetall("label:" + username + ":" + uid)
    if not label:
        return {"error" : "No label found with this id"}, 400
    links = []

    if label["state"] != "locked":
        links.append(Link("label:delete", request.script_root + request.full_path))
    doc = Document(data={"item" : label}, links=links).to_json()

    return doc

@app.route("/labels/<uid>", methods=["DELETE"])
def labels_delete(uid):
    if not is_sender_authorized():
        logUnauthorized()
        return _unauthorized
    
    username = g.authorization["username"]
    label_to_delete = db.hgetall("label:" + username + ":" + uid)
    if not label_to_delete:
        return {"error" : "No label found with this id"}, 400
    if label_to_delete["state"] == "locked":
        return {"error" : "This label cannot be deleted"}, 400

    db.delete("label:" + username + ":" + uid)

    res = make_response("", 204)
    return res

if __name__ == "__main__":
    app.run()