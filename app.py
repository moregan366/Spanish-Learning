from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

import os
import psycopg2

app = Flask(__name__, template_folder="Templates")
CORS(app)

# Get database URL from Render environment
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# ------------------------
# Home page (UI)
# ------------------------

@app.route("/")
def home():
    return render_template("index.html")

# ------------------------
# Add flashcard
# ------------------------
@app.route("/add", methods=["POST"])
def add_flashcard():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400

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

    return jsonify({"message": "Flashcard added!"})

# ------------------------
# Get all flashcards
# ------------------------
@app.route("/cards", methods=["GET"])
def get_cards():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT id, "Spanish", "English" FROM "Flashcards"')
    rows = cur.fetchall()

    cards = []
    for row in rows:
        cards.append({
            "id": row[0],
            "front": row[1],
            "back": row[2]
        })

    cur.close()
    conn.close()

    return jsonify(cards)

# ------------------------
# Delete card
# ------------------------
@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_card(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute('DELETE FROM "Flashcards" WHERE id = %s', (id,))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"message": "Card deleted"})

# ------------------------
# Delete card
# ------------------------
@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

# ------------------------
# Spanish Writing
# ------------------------
@app.route("/writing")
def writing():
    return render_template("writing.html")

# ------------------------
# Run app
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

