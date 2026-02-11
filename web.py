from flask import Flask, request, redirect, render_template_string
import json
import os
import datetime

app = Flask(__name__)

DATA_FILE = "premium_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def home():
    data = load_data()

    html = """
    <h1>👑 ZENO Premium Dashboard</h1>
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
    user_id = request.form["user_id"]
    data = load_data()

    if user_id in data:
        del data[user_id]
        save_data(data)

    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
