from flask import Flask, render_template_string, redirect, request, session
import json
import os
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")

ADMIN_USER = os.environ.get("ADMIN_USER")
ADMIN_PASS = os.environ.get("ADMIN_PASS")

DATA_FILE = "premium_data.json"

# -------------------------
# Load Data
# -------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# -------------------------
# Login
# -------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")

        if user == ADMIN_USER and pw == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")
        else:
            return "❌ Login Failed"

    return """
    <h2>🔐 Admin Login</h2>
    <form method="post">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button type="submit">Login</button>
    </form>
    """

# -------------------------
# Dashboard
# -------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    data = load_data()
    now = datetime.datetime.now(datetime.UTC)

    rows = ""
    total = len(data)

    for user_id, info in data.items():
        expiry = datetime.datetime.fromisoformat(info["expiry"])
        remaining = expiry - now

        if remaining.total_seconds() <= 0:
            status = "🔴 Expired"
            color = "#ff4d4d"
        elif remaining <= datetime.timedelta(days=3):
            status = "🟡 Expiring Soon"
            color = "#ffd633"
        else:
            status = "🟢 Active"
            color = "#3ef2c5"

        rows += f"""
        <tr>
            <td>{user_id}</td>
            <td>{info['package'].upper()}</td>
            <td>{expiry.strftime('%d/%m/%Y %H:%M')}</td>
            <td style='color:{color}; font-weight:bold'>{status}</td>
            <td>
                <a href="/remove/{user_id}" style="color:red">Remove</a>
            </td>
        </tr>
        """

    return f"""
    <h2>👑 Premium Dashboard</h2>
    <p>📦 Total Members: {total}</p>
    <table border="1" cellpadding="10">
        <tr>
            <th>User ID</th>
            <th>Package</th>
            <th>Expiry</th>
            <th>Status</th>
            <th>Action</th>
        </tr>
        {rows}
    </table>
    <br>
    <a href="/logout">Logout</a>
    """

# -------------------------
# Remove Premium
# -------------------------
@app.route("/remove/<user_id>")
def remove(user_id):
    if not session.get("admin"):
        return redirect("/")

    data = load_data()
    if user_id in data:
        del data[user_id]
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    return redirect("/dashboard")

# -------------------------
# Logout
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
