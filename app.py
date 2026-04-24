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
    tense = request.args.get("tense")

    if tense == "present":
        story = [
            {"english": "I arrive at the airport.", "spanish": "Llego al aeropuerto."},
            {"english": "It is very busy.", "spanish": "Está muy ocupado."},
            {"english": "I look for my gate.", "spanish": "Busco mi puerta."},
            {"english": "I buy a coffee.", "spanish": "Compro un café."},
            {"english": "The flight is delayed.", "spanish": "El vuelo se retrasa."},
            {"english": "I sit and wait.", "spanish": "Me siento y espero."},
            {"english": "I meet a friendly person.", "spanish": "Conozco a una persona amable."},
            {"english": "We talk.", "spanish": "Hablamos."},
            {"english": "We board.", "spanish": "Embarcamos."},
            {"english": "The journey begins.", "spanish": "El viaje comienza."}
        ]

    elif tense == "preterite":
        story = [
            {"english": "I arrived at the airport.", "spanish": "Llegué al aeropuerto."},
            {"english": "It was very busy.", "spanish": "Estaba muy ocupado."},
            {"english": "I looked for my gate.", "spanish": "Busqué mi puerta."},
            {"english": "I bought a coffee.", "spanish": "Compré un café."},
            {"english": "The flight was delayed.", "spanish": "El vuelo se retrasó."},
            {"english": "I sat and waited.", "spanish": "Me senté y esperé."},
            {"english": "I met a friendly person.", "spanish": "Conocí a una persona amable."},
            {"english": "We started talking.", "spanish": "Empezamos a hablar."},
            {"english": "We boarded.", "spanish": "Embarcamos."},
            {"english": "The journey began.", "spanish": "El viaje comenzó."}
        ]

    elif tense == "future":
        story = [
            {"english": "I will arrive at the airport.", "spanish": "Llegaré al aeropuerto."},
            {"english": "It will be busy.", "spanish": "Estará ocupado."},
            {"english": "I will look for my gate.", "spanish": "Buscaré mi puerta."},
            {"english": "I will buy a coffee.", "spanish": "Compraré un café."},
            {"english": "The flight will be delayed.", "spanish": "El vuelo se retrasará."},
            {"english": "I will sit and wait.", "spanish": "Me sentaré y esperaré."},
            {"english": "I will meet someone.", "spanish": "Conoceré a alguien."},
            {"english": "We will talk.", "spanish": "Hablaremos."},
            {"english": "We will board.", "spanish": "Embarcaremos."},
            {"english": "The journey will begin.", "spanish": "El viaje comenzará."}
        ]

    else:
        # mixed
        story = [
            {"english": "I arrived at the airport.", "spanish": "Llegué al aeropuerto."},
            {"english": "It was busy.", "spanish": "Estaba ocupado."},
            {"english": "I buy a coffee.", "spanish": "Compro un café."},
            {"english": "I will sit down.", "spanish": "Me sentaré."},
            {"english": "I was waiting.", "spanish": "Estaba esperando."},
            {"english": "I met someone.", "spanish": "Conocí a alguien."},
            {"english": "We talk.", "spanish": "Hablamos."},
            {"english": "We will board soon.", "spanish": "Embarcaremos pronto."},
            {"english": "The journey begins.", "spanish": "El viaje comienza."},
            {"english": "It was a good day.", "spanish": "Fue un buen día."}
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

