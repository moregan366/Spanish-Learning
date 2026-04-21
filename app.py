from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2

app = Flask(__name__)
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
    return """
    <html>
        <head>
            <title>Spanish Learning</title>
        </head>
        <body>
            <h1>Spanish Flashcards</h1>

            <h2>Add a new card</h2>
            <input id="front" placeholder="Spanish">
            <input id="back" placeholder="English">
            <button onclick="addCard()">Add</button>

            <h2>Cards</h2>
            <ul id="cards"></ul>

            <script>
                async function loadCards() {
                    const res = await fetch('/cards');
                    const data = await res.json();

                    const list = document.getElementById('cards');
                    list.innerHTML = '';

                    data.forEach(card => {
                        const li = document.createElement('li');
                        li.textContent = card.front + " - " + card.back;
                        list.appendChild(li);
                    });
                }

                async function addCard() {
                    const button = document.querySelector("button");
                    button.disabled = true;

                    const front = document.getElementById('front').value;
                    const back = document.getElementById('back').value;

                    await fetch('/add', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ front, back })
                    });

                    document.getElementById('front').value = "";
                    document.getElementById('back').value = "";

                    await loadCards();

                    button.disabled = false;
}


                loadCards();
            </script>
        </body>
    </html>
    """

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

    cur.close()
    conn.close()

    cards = []
    for row in rows:
        cards.append({
            "id": row[0],
            "front": row[1],   # Spanish
            "back": row[2]     # English
        })

    return jsonify(cards)

# ------------------------
# Run app
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

