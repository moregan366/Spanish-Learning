from flask import Flask, request, jsonify
import os
import psycopg2

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def home():
    return "Spanish Learning App is running!"

@app.route("/add", methods=["POST"])
def add_flashcard():
    data = request.json
    front = data.get("front")
    back = data.get("back")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO flashcards (front, back) VALUES (%s, %s)",
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

