from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, send, join_room, close_room
from dotenv import load_dotenv
from os import getenv
from jwt import decode, InvalidTokenError, encode
from datetime import datetime
from redis import StrictRedis
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

load_dotenv()

JWT_SECRET = getenv("JWT_SECRET")
REDIS_HOST = getenv("REDIS_HOST")
REDIS_PASS = getenv("REDIS_PASS")
db = StrictRedis(host=REDIS_HOST, port=6379, db=13, password=REDIS_PASS)

app = Flask(__name__)
app.config["SECRET_KEY"] = getenv("SOCKET_SECRET")
socketio = SocketIO(app, cors_allowed_origins="https://gentle-headland-67122.herokuapp.com")

user_rooms = {} # {"room name equal to username" : [ list of connected users (sids) ] , etc.}

@socketio.on("login")
def login(data):
    if not "token" in data:
        emit("error", {"error" : "Invalid token"})
        return
    token = data["token"]
    try:
        payload = decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        emit("error", {"error" : "Invalid token"})
        return

    if any(x not in payload for x in ["type", "username", "iat", "exp"]):
        emit("error", {"error" : "Invalid token"})
        return

    if payload["type"] != "socketiotoken":
        emit("error", {"error" : "Invalid token"})
        return

    try:
        if datetime.fromtimestamp(payload["exp"]) < datetime.now():
            emit("error", {"error" : "Token expired"})
            return
    except Exception:
        emit("error", {"error" : "Invalid token"})
        return

    username = payload["username"]
    if username.startswith("auth0|") or username.startswith("google-oauth2|"):
        if not db.keys(username):
            emit("error", {"error" : "Invalid token"})
            return
    else:
        if not db.keys("username:" + username):
            emit("error", {"error" : "Invalid token"})
            return

    join_room(username)
    if not username in user_rooms:
        user_rooms[username] = [request.sid]
    else:
        user_rooms[username].append(request.sid)

    emit("success", {"success" : "Logged in"})

@socketio.on("disconnect")
def disconnect():
    for room in user_rooms:
        if request.sid in user_rooms[room]:
            user_rooms[room].remove(request.sid)
            break

def send_notifications():
    try:
        for username in list(user_rooms):
            if not user_rooms[username]:
                user_rooms.pop(username)
                continue
            notifs = db.lrange("notifications:" + username, 0, -1)
            if notifs:
                db.delete("notifications:" + username)
                for notif in notifs:
                    socketio.emit('message', {"notification" : notif.decode()}, room=username)
    except Exception:
        pass
            

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_notifications, trigger="interval", seconds=3)
scheduler.start()

if __name__ == "__main__":
    app.run(port=3000)

atexit.register(lambda: scheduler.shutdown())