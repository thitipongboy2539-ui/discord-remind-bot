from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 VIP BOT DASHBOARD RUNNING"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
