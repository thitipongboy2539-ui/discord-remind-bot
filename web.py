import json
import os
import random
from flask import Flask, render_template_string, request, redirect, session

app = Flask(__name__)
app.secret_key = "Zenomodshop20"

DATA_FILE = "data.json"

USERNAME = "Zenodesign"
PASSWORD = "Boyying2539"

otp_storage = {}  # เก็บ OTP ชั่วคราว

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "pending": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            otp = str(random.randint(100000, 999999))
            otp_storage["otp"] = otp
            print(f"🔐 OTP CODE: {otp}")  # ดู OTP ใน Railway Logs
            return redirect("/verify")
        else:
            return "❌ Wrong Username or Password"

    return """
    <h2>🔐 Admin Login</h2>
    <form method="post">
        Username: <input type="text" name="username"><br><br>
        Password: <input type="password" name="password"><br><br>
        <button type="submit">Login</button>
    </form>
    """

@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        user_otp = request.form.get("otp")

        if user_otp == otp_storage.get("otp"):
            session["logged_in"] = True
            otp_storage.clear()
            return redirect("/")
        else:
            return "❌ Invalid OTP"

    return """
    <h2>🔑 Enter OTP</h2>
    <form method="post">
        OTP: <input type="text" name="otp"><br><br>
        <button type="submit">Verify</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/login")

    data = load_data()
    users = data.get("users", {})
    pending = data.get("pending", {})

    vip_count = sum(1 for u in users.values() if u["role"] == "VIP")
    gold_count = sum(1 for u in users.values() if u["role"] == "Gold")

    html = """
    <h1>👑 BOT DASHBOARD (2FA ENABLED)</h1>
    <a href="/logout">Logout</a>

    <h2>📊 Statistics</h2>
    <ul>
        <li>VIP: {{vip}}</li>
        <li>Gold: {{gold}}</li>
        <li>Pending: {{pending}}</li>
    </ul>

    <h2>📋 Members</h2>
    <table border="1" cellpadding="5">
        <tr>
            <th>User ID</th>
            <th>Role</th>
            <th>Expiry</th>
        </tr>
        {% for uid, info in users.items() %}
        <tr>
            <td>{{uid}}</td>
            <td>{{info.role}}</td>
            <td>{{info.expiry}}</td>
        </tr>
        {% endfor %}
    </table>
    """

    return render_template_string(
        html,
        vip=vip_count,
        gold=gold_count,
        pending=len(pending),
        users=users
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
