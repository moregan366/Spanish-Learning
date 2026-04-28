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

    conn = get_db()
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

    # ✅ SAVE STORY (FIXED)

    conn = get_db()
    cur = conn.cursor()

    title = story[0]["english"][:40] if story else "Untitled story"

    cur.execute("""
        INSERT INTO stories (title, topic, level, tense, content)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        title,
        topic,
        level,
        tense,
        json.dumps(story)
    ))

    story_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "story": story,
        "id": story_id
    })

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
        SELECT id, title, content, score, feedback, progress_index, progress_results
        FROM stories
        WHERE 
            TRIM(LOWER(topic)) = TRIM(LOWER(%s))
        AND TRIM(LOWER(level)) = TRIM(LOWER(%s))
        AND TRIM(LOWER(tense)) = TRIM(LOWER(%s))
        ORDER BY created_at DESC
        LIMIT 50
    """, (topic, level, tense))

    rows = cur.fetchall()

    print("Rows from DB:", rows)  # 👈 debug (keep this)

    stories = []

    for r in rows:
        content = r[2]

        # ✅ Handle both string + jsonb safely
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except:
                content = []  # fallback instead of crashing

        # ✅ Handle progress_results safely
        progress_results = []
        if r[6]:
            try:
                progress_results = json.loads(r[6])
            except:
                progress_results = []

        # ✅ ALWAYS append (no skipping rows)
        stories.append({
            "id": r[0],
            "title": r[1],
            "content": content,
            "score": r[3],
            "feedback": r[4],
            "progress_index": r[5],
            "progress_results": progress_results
        })

    cur.close()
    conn.close()

    return jsonify(stories)

# ------------------------
# Check Writing
# ------------------------
@app.route("/check_writing", methods=["POST"])
def check_writing():
    data = request.json
    user = data["user"].strip()
    correct = data["correct"].strip()

    prompt = f"""
You are a Spanish teacher.

A student is translating a sentence into Spanish.

Correct answer:
"{correct}"

Student answer:
"{user}"

Your job:

1. Decide if the student's answer is ACCEPTABLE.
   - Allow small variations (synonyms, word order, etc.)
   - Ignore missing punctuation like full stops
   - Minor grammar mistakes can still be acceptable if meaning is clear

2. If acceptable → return:
CORRECT

3. If not acceptable → return:
INCORRECT: followed by a short, helpful explanation and the improved version

Be encouraging and educational.
Keep feedback concise.

Also briefly explain the key mistake (e.g. tense, gender, verb choice).

Examples:

CORRECT

INCORRECT: You used the wrong verb tense. A better answer would be "Voy a la tienda."
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content.strip()

        if result.startswith("CORRECT"):
            return jsonify({"correct": True})
        else:
            feedback = result.replace("INCORRECT:", "").strip()
            return jsonify({
                "correct": False,
                "feedback": feedback
            })

    except Exception as e:
        print("ERROR in check_writing:", e)
        return jsonify({
            "correct": False,
            "feedback": "Error checking answer. Try again."
        })

# ------------------------
# Complete Story
# ------------------------
@app.route("/complete_story", methods=["POST"])
def complete_story():
    try:
        data = request.json
        results = data["results"]

        total = len(results)
        correct_count = sum(1 for r in results if r["correct"])
        score = int((correct_count / total) * 100) if total > 0 else 0

        # Build AI summary
        mistakes = [
            f'User: {r["user"]} | Correct: {r["correctAnswer"]}'
            for r in results if not r["correct"]
        ]

        mistake_text = "\n".join(mistakes[:5]) or "None"

        prompt = f"""
You are a Spanish teacher.

A student completed a writing exercise.

Score: {score}%

Here are some of their mistakes:
{mistake_text}

Write a short summary of:
- What they did well
- What they should focus on improving

Keep it concise and encouraging.
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        feedback = response.choices[0].message.content.strip()

        # Save to DB
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE stories
            SET score = %s,
                feedback = %s
            WHERE id = (
                SELECT id FROM stories
                WHERE LOWER(topic)=LOWER(%s)
                  AND LOWER(level)=LOWER(%s)
                  AND LOWER(tense)=LOWER(%s)
                ORDER BY created_at DESC
                LIMIT 1
            )
        """, (score, feedback, data["topic"], data["level"], data["tense"]))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "score": score,
            "feedback": feedback
        })

    except Exception as e:
        print("ERROR in complete_story:", e)
        return jsonify({"error": str(e)}), 500

# ------------------------
# Results page
# ------------------------
@app.route("/results")
def results_page():
    score = request.args.get("score")
    feedback = request.args.get("feedback")

    return render_template("results.html", score=score, feedback=feedback)

# ------------------------
# Delete Story
# ------------------------
@app.route("/delete_story/<int:id>", methods=["DELETE"])
def delete_story(id):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("DELETE FROM stories WHERE id = %s", (id,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"status": "deleted"})

    except Exception as e:
        print("ERROR deleting story:", e)
        return jsonify({"error": str(e)}), 500

# ------------------------
# Save Progress
# ------------------------
@app.route("/save_progress/<int:id>", methods=["POST"])
def save_progress(id):
    data = request.json
    index = data.get("index", 0)
    results = json.dumps(data.get("results", []))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE stories
        SET progress_index = %s,
            progress_results = %s
        WHERE id = %s
    """, (index, results, id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "saved"})

# ------------------------
# Spanish Listening
# ------------------------
@app.route("/listening")
def listening():
    return render_template("listening.html")

# ------------------------
# Run app
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

