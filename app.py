from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

import os
import json
import psycopg2
import random

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not set in environment variables")

client = OpenAI(api_key=api_key)

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

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT content
    FROM stories
    WHERE LOWER(topic)=LOWER(%s)
    AND LOWER(level)=LOWER(%s)
    AND LOWER(tense)=LOWER(%s)
    ORDER BY created_at DESC
    LIMIT 5
    """, (topic, level, tense))

    existing = [r[0] for r in cur.fetchall()]
    existing_text = "\n".join(str(e) for e in existing)

    cur.close()
    conn.close()
    
    random_hint = random.choice([
    "The story happens at an airport.",
    "The story happens in a restaurant.",
    "The story happens in a hotel.",
    "The story happens while walking in a city.",
    "The story happens on a train."
    ])
    
    prompt = f"""
    Create a Spanish learning story.

    Topic: {topic}
    Level: {level}
    Tense: {tense}

    IMPORTANT:
    Do NOT repeat or resemble any of these previous stories:

    ---
    {existing_text}
    ---
    
    Make this story clearly different by:
    - Using a different setting (e.g. airport, hotel, restaurant, city walk)
    - Using different verbs and vocabulary
    - Avoiding phrases like "I travel to Spain"

    Story idea: {random_hint}

    Keep it appropriate for {level} learners.

    Generate EXACTLY 10 short, connected sentences that form a coherent story.

    Each line MUST follow this format:
    English | Spanish

    Do not include numbering.
    Do not include extra text.

    Example:
    I go to the store. | Voy a la tienda.
    """
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content

    story = []
    lines = text.split("\n")

    for line in lines:
        if "|" in line:
            english, spanish = line.split("|", 1)
            story.append({
                "english": english.strip(),
                "spanish": spanish.strip()
            })

    # ✅ SAVE STORIES

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    title = story[0]["english"][:40] if story else "Untitled story"

    cur.execute("""
        INSERT INTO stories (title, topic, level, tense, content)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        title,
        topic,
        level,
        tense,
        json.dumps(story)
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(story)

# ------------------------
# Get Stories
# ------------------------
@app.route("/get_stories")
def get_stories():
    topic = request.args.get("topic") or ""
    level = request.args.get("level") or ""
    tense = request.args.get("tense") or ""

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, content
        FROM stories
        WHERE LOWER(topic)=LOWER(%s)
          AND LOWER(level)=LOWER(%s)
          AND LOWER(tense)=LOWER(%s)
        ORDER BY created_at DESC
        LIMIT 10
    """, (topic, level, tense))


    rows = cur.fetchall()

    print("Rows from DB:", rows)  # 👈 debug (keep this)

    stories = []

    for r in rows:
        try:
            content = r[2]

            # If it's a string → parse it
            if isinstance(content, str):
                content = json.loads(content)

            stories.append({
                "id": r[0],
                "title": r[1],
                "content": content
            })

        except Exception as e:
            print("ERROR parsing story:", e)

    cur.close()
    conn.close()

    return jsonify(stories)

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

