import os
from flask import Flask, render_template_string, request, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallbacksecret")

ADMIN_USER = os.environ.get("ADMIN_USER")
ADMIN_PASS = os.environ.get("ADMIN_PASS")

# ================= LOGIN PAGE =================
login_page = """
<h2>🔐 ZENO Dashboard Login</h2>
<form method="POST">
    <input type="text" name="username" placeholder="Username" required><br><br>
    <input type="password" name="password" placeholder="Password" required><br><br>
    <button type="submit">Login</button>
</form>
<p style="color:red;">{{ error }}</p>
"""

# ================= DASHBOARD =================
dashboard_page = """
<h2>👑 ZENO Dashboard</h2>
<p>Login สำเร็จแล้ว</p>
<a href="/logout">Logout</a>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        print("Input:", username, password)
        print("Env:", ADMIN_USER, ADMIN_PASS)

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")
        else:
            error = "❌ Login Failed"

    return render_template_string(login_page, error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")
    return render_template_string(dashboard_page)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
