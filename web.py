import json
import os
from flask import Flask, render_template_string, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # เปลี่ยนเป็นอะไรก็ได้

DATA_FILE = "data.json"

USERNAME = "Zenodesign"
PASSWORD = "Boyying202539"   # เปลี่ยนรหัสเองได้

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
            session["logged_in"] = True
            return redirect("/")
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
    <h1>👑 BOT DASHBOARD</h1>
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
