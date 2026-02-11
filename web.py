from flask import Flask, request, redirect, render_template_string, session
import json
import os
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

DATA_FILE = "premium_data.json"

ADMIN_USER = os.environ.get("ADMIN_USER")
ADMIN_PASS = os.environ.get("ADMIN_PASS")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_logged_in():
    return session.get("logged_in")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            return redirect("/")
        else:
            return "❌ Login Failed"

    return """
    <h2>🔐 Admin Login</h2>
    <form method="post">
        Username:<br>
        <input type="text" name="username"><br><br>
        Password:<br>
        <input type="password" name="password"><br><br>
        <button type="submit">Login</button>
    </form>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def home():
    if not is_logged_in():
        return redirect("/login")

    data = load_data()

    html = """
    <h1>👑 ZENO Premium Dashboard</h1>
    <a href="/logout">🚪 Logout</a>
    <table border="1" cellpadding="10">
        <tr>
            <th>User ID</th>
            <th>Package</th>
            <th>Expiry</th>
            <th>Action</th>
        </tr>
    """

    for user_id, info in data.items():
        html += f"""
        <tr>
            <td>{user_id}</td>
            <td>{info['package']}</td>
            <td>{info['expiry']}</td>
            <td>
                <form action="/extend" method="post" style="display:inline;">
                    <input type="hidden" name="user_id" value="{user_id}">
                    <button type="submit">➕ +30 วัน</button>
                </form>

                <form action="/remove" method="post" style="display:inline;">
                    <input type="hidden" name="user_id" value="{user_id}">
                    <button type="submit">❌ Remove</button>
                </form>
            </td>
        </tr>
        """

    html += """
    </table>

    <h2>➕ เพิ่มสมาชิกใหม่</h2>
    <form action="/add" method="post">
        User ID: <input type="text" name="user_id"><br><br>
        Package:
        <select name="package">
            <option value="VIP">VIP</option>
            <option value="Gold">Gold</option>
        </select><br><br>
        <button type="submit">เพิ่ม</button>
    </form>
    """

    return render_template_string(html)


@app.route("/add", methods=["POST"])
def add():
    if not is_logged_in():
        return redirect("/login")

    user_id = request.form["user_id"]
    package = request.form["package"]

    data = load_data()

    expiry = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)

    data[user_id] = {
        "package": package,
        "expiry": expiry.isoformat()
    }

    save_data(data)
    return redirect("/")


@app.route("/extend", methods=["POST"])
def extend():
    if not is_logged_in():
        return redirect("/login")

    user_id = request.form["user_id"]
    data = load_data()

    if user_id in data:
        old_expiry = datetime.datetime.fromisoformat(data[user_id]["expiry"])
        new_expiry = old_expiry + datetime.timedelta(days=30)
        data[user_id]["expiry"] = new_expiry.isoformat()
        save_data(data)

    return redirect("/")


@app.route("/remove", methods=["POST"])
def remove():
    if not is_logged_in():
        return redirect("/login")

    user_id = request.form["user_id"]
    data = load_data()

    if user_id in data:
        del data[user_id]
        save_data(data)

    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
