from flask import Flask, redirect, request, session
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
# Login Page
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
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 flex items-center justify-center h-screen text-white">
        <div class="bg-gray-800 p-8 rounded-2xl shadow-xl w-96">
            <h2 class="text-2xl font-bold mb-6 text-center">🔐 Admin Login</h2>
            <form method="post" class="space-y-4">
                <input name="username" placeholder="Username"
                    class="w-full p-3 rounded bg-gray-700 focus:outline-none">
                <input name="password" type="password" placeholder="Password"
                    class="w-full p-3 rounded bg-gray-700 focus:outline-none">
                <button class="w-full bg-emerald-500 hover:bg-emerald-600 p-3 rounded font-bold">
                    Login
                </button>
            </form>
        </div>
    </body>
    </html>
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

    total = len(data)
    vip_count = 0
    gold_count = 0

    rows = ""

    for user_id, info in data.items():
        expiry = datetime.datetime.fromisoformat(info["expiry"])
        remaining = expiry - now

        if info["package"] == "vip":
            vip_count += 1
        else:
            gold_count += 1

        if remaining.total_seconds() <= 0:
            status = "Expired"
            color = "text-red-400"
        elif remaining <= datetime.timedelta(days=3):
            status = "Expiring Soon"
            color = "text-yellow-400"
        else:
            status = "Active"
            color = "text-emerald-400"

        rows += f"""
        <tr class="border-b border-gray-700 hover:bg-gray-800">
            <td class="p-3">{user_id}</td>
            <td class="p-3 uppercase">{info['package']}</td>
            <td class="p-3">{expiry.strftime('%d/%m/%Y %H:%M')}</td>
            <td class="p-3 font-bold {color}">{status}</td>
            <td class="p-3">
                <a href="/remove/{user_id}" 
                   class="bg-red-500 hover:bg-red-600 px-3 py-1 rounded text-sm">
                   Remove
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white min-h-screen p-8">

        <div class="max-w-6xl mx-auto">

            <h1 class="text-3xl font-bold mb-8">👑 Premium Enterprise Dashboard</h1>

            <!-- Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                <div class="bg-gray-800 p-6 rounded-2xl shadow">
                    <h2 class="text-gray-400">Total Members</h2>
                    <p class="text-3xl font-bold mt-2">{total}</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-2xl shadow">
                    <h2 class="text-gray-400">VIP Members</h2>
                    <p class="text-3xl font-bold text-emerald-400 mt-2">{vip_count}</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-2xl shadow">
                    <h2 class="text-gray-400">Gold Members</h2>
                    <p class="text-3xl font-bold text-yellow-400 mt-2">{gold_count}</p>
                </div>
            </div>

            <!-- Table -->
            <div class="bg-gray-800 rounded-2xl shadow overflow-hidden">
                <table class="w-full text-left">
                    <thead class="bg-gray-700 text-gray-300">
                        <tr>
                            <th class="p-3">User ID</th>
                            <th class="p-3">Package</th>
                            <th class="p-3">Expiry</th>
                            <th class="p-3">Status</th>
                            <th class="p-3">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>

            <div class="mt-8">
                <a href="/logout" 
                   class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded">
                   Logout
                </a>
            </div>

        </div>

    </body>
    </html>
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
