from flask import Flask, render_template, redirect
import json
import os
import datetime

app = Flask(__name__)

DATA_FILE = "premium.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def format_time(iso):
    dt = datetime.datetime.fromisoformat(iso)
    return dt.strftime("%d/%m/%Y %H:%M")

@app.route("/")
def dashboard():
    data = load_data()
    return render_template("dashboard.html", members=data, format_time=format_time)

@app.route("/delete/<int:user_id>")
def delete_member(user_id):
    data = load_data()
    data = [x for x in data if x["user_id"] != user_id]

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
