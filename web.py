from flask import Flask, render_template_string
import json
import os

app = Flask(__name__)

DATA_FILE = "premium_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

@app.route("/")
def dashboard():

    data = load_data()

    html = """
    <h1>👑 Premium Dashboard</h1>
    <table border="1" cellpadding="10">
        <tr>
            <th>User ID</th>
            <th>Package</th>
            <th>Expiry</th>
        </tr>
        {% for user_id, info in data.items() %}
        <tr>
            <td>{{ user_id }}</td>
            <td>{{ info.package }}</td>
            <td>{{ info.expiry }}</td>
        </tr>
        {% endfor %}
    </table>
    """

    return render_template_string(html, data=data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
