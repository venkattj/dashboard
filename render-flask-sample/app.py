from datetime import datetime
import random

from flask import Flask, jsonify, render_template

app = Flask(__name__)

QUOTES = [
    "Curiosity powers every innovation.",
    "Every deploy is a checkpoint toward learning more.",
    "Keep it simple, measurable, and observable.",
    "Great UIs start with clear data and calm design.",
    "APIs succeed when they stay tiny and predictable."
]

@app.route("/")
def home():
    snapshot = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return render_template("index.html", now=snapshot)

@app.get("/api/quote")
def quote():
    quote = random.choice(QUOTES)
    return jsonify({
        "quote": quote,
        "author": "Render Sample App",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@app.get("/api/stats")
def stats():
    return jsonify({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "active_users": random.randint(60, 200),
        "conversion_rate": round(random.uniform(0.03, 0.12), 3),
        "region_breakdown": {
            "Americas": random.randint(20, 80),
            "EMEA": random.randint(15, 60),
            "APAC": random.randint(10, 50)
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
