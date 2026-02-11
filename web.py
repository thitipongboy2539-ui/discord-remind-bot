from flask import Flask, redirect, request, session
import json
import os
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")

ADMIN_USER = os.environ.get("ADMIN_USER")
ADMIN_PASS = os.environ.get("ADMIN_PASS")

DATA_FILE = "premium_data.json"

VIP_PRICE = 200
GOLD_PRICE = 100

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
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 flex items-center justify-center h-screen text-white">
        <div class="bg-gray-900 p-8 rounded-2xl shadow-2xl w-96">
            <h2 class="text-2xl font-bold mb-6 text-center">🔐 Admin Login</h2>
            <form method="post" class="space-y-4">
                <input name="username" placeholder="Username"
                    class="w-full p-3 rounded bg-gray-800 focus:outline-none">
                <input name="password" type="password" placeholder="Password"
                    class="w-full p-3 rounded bg-gray-800 focus:outline-none">
                <button class="w-full bg-emerald-500 hover:bg-emerald-600 p-3 rounded font-bold">
                    Login
                </button>
            </form>
        </div>
    </body>
    </html>
    """

# -------------------------
# Dashboard v2
# -------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    data = load_data()
    now = datetime.datetime.now(datetime.UTC)
    search = request.args.get("search", "")

    vip_count = 0
    gold_count = 0
    total_revenue = 0

    rows = ""

    for user_id, info in data.items():

        if search and search not in user_id:
            continue

        expiry = datetime.datetime.fromisoformat(info["expiry"])
        remaining = expiry - now

        if info["package"] == "vip":
            vip_count += 1
            total_revenue += VIP_PRICE
        else:
            gold_count += 1
            total_revenue += GOLD_PRICE

        if remaining.total_seconds() <= 0:
            badge = '<span class="bg-red-500 px-2 py-1 rounded text-xs">Expired</span>'
        elif remaining <= datetime.timedelta(days=3):
            badge = '<span class="bg-yellow-500 px-2 py-1 rounded text-xs">Expiring</span>'
        else:
            badge = '<span class="bg-emerald-500 px-2 py-1 rounded text-xs">Active</span>'

        rows += f"""
        <tr class="border-b border-gray-800 hover:bg-gray-900">
            <td class="p-3">{user_id}</td>
            <td class="p-3 uppercase">{info['package']}</td>
            <td class="p-3">{expiry.strftime('%d/%m/%Y %H:%M')}</td>
            <td class="p-3">{badge}</td>
            <td class="p-3">
                <a href="/remove/{user_id}" 
                   class="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm">
                   Remove
                </a>
            </td>
        </tr>
        """

    total_members = vip_count + gold_count

    return f"""
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-950 text-white min-h-screen p-8">

        <div class="max-w-7xl mx-auto">

            <h1 class="text-3xl font-bold mb-8">👑 Premium Enterprise v2</h1>

            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
                <div class="bg-gray-900 p-6 rounded-2xl shadow">
                    <h2 class="text-gray-400">Total Members</h2>
                    <p class="text-3xl font-bold mt-2">{total_members}</p>
                </div>
                <div class="bg-gray-900 p-6 rounded-2xl shadow">
                    <h2 class="text-gray-400">VIP</h2>
                    <p class="text-3xl font-bold text-emerald-400 mt-2">{vip_count}</p>
                </div>
                <div class="bg-gray-900 p-6 rounded-2xl shadow">
                    <h2 class="text-gray-400">Gold</h2>
                    <p class="text-3xl font-bold text-yellow-400 mt-2">{gold_count}</p>
                </div>
                <div class="bg-gray-900 p-6 rounded-2xl shadow">
                    <h2 class="text-gray-400">Revenue</h2>
                    <p class="text-3xl font-bold text-purple-400 mt-2">฿{total_revenue}</p>
                </div>
            </div>

            <!-- Chart -->
            <div class="bg-gray-900 p-6 rounded-2xl shadow mb-10">
                <canvas id="myChart"></canvas>
            </div>

            <!-- Search -->
            <form method="get" class="mb-6">
                <input name="search" placeholder="Search User ID..."
                    class="p-3 rounded bg-gray-800 w-80">
                <button class="bg-blue-600 px-4 py-3 rounded">Search</button>
                <a href="/dashboard" class="ml-3 text-gray-400">Reset</a>
            </form>

            <!-- Table -->
            <div class="bg-gray-900 rounded-2xl shadow overflow-hidden">
                <table class="w-full text-left">
                    <thead class="bg-gray-800 text-gray-300">
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
                <a href="/logout" class="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded">
                    Logout
                </a>
            </div>

        </div>

        <script>
        const ctx = document.getElementById('myChart');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['VIP', 'Gold'],
                datasets: [{{
                    data: [{vip_count}, {gold_count}],
                    backgroundColor: ['#10B981', '#FACC15']
                }}]
            }}
        }});
        </script>

    </body>
    </html>
    """

# -------------------------
# Remove
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
