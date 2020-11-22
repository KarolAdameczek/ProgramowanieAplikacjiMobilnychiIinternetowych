from flask import Flask, render_template
app = Flask(__name__)
app.debug = False

@app.route("/")
def check():
    return render_template("index.html")

@app.route("/sender/sign-up")
def index():
    return render_template("sign-up.html")

if __name__ == "__main__":
    app.run()