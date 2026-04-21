from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def home():
    return "Spanish Learning App is running!"

@app.route("/add", methods=["POST"])
def add_flashcard():
    data = request.get_json()

    if not data:
        return {"error": "No JSON received"}, 400

    front = data.get("front")
    back = data.get("back")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        'INSERT INTO "Flashcards" ("Spanish", "English") VALUES (%s, %s)',
        (front, back)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Flashcard added!"}

@app.route("/cards", methods=["GET"])
def get_cards():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, front, back FROM flashcards")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    cards = [{"id": r[0], "front": r[1], "back": r[2]} for r in rows]
    return jsonify(cards)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

