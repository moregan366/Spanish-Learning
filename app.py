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
@app.route("/add_flashcard", methods=["POST"])
def add_flashcard():
    data = request.json

    english = data["front"]
    spanish = data["back"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        'INSERT INTO "Flashcards" ("English", "Spanish") VALUES (%s, %s)',
        (english, spanish)
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})

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
# Generate Story
# ------------------------
@app.route("/generate_story")
def generate_story():
    topic = request.args.get("topic")
    level = request.args.get("level")

    story = [
        {"english": "I arrived at the airport.", "spanish": "Llegué al aeropuerto."},
        {"english": "It was very busy.", "spanish": "Estaba muy ocupado."},
        {"english": "I looked for my gate.", "spanish": "Busqué mi puerta."},
        {"english": "I bought a coffee.", "spanish": "Compré un café."},
        {"english": "The flight was delayed.", "spanish": "El vuelo se retrasó."},
        {"english": "I sat down and waited.", "spanish": "Me senté y esperé."},
        {"english": "I met a friendly person.", "spanish": "Conocí a una persona amable."},
        {"english": "We started talking.", "spanish": "Empezamos a hablar."},
        {"english": "Finally, we boarded.", "spanish": "Finalmente, embarcamos."},
        {"english": "The journey began.", "spanish": "El viaje comenzó."}
    ]

    return jsonify(story)

# ------------------------
# Check Writing
# ------------------------
@app.route("/check_writing", methods=["POST"])
def check_writing():
    data = request.json
    user = data["user"].lower().strip()
    correct = data["correct"].lower().strip()

    if user == correct:
        return jsonify({"correct": True})
    else:
        return jsonify({
            "correct": False,
            "feedback": correct
        })

# ------------------------
# Run app
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

