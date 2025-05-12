from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import json
import sqlite3
import re
from flask import flash, make_response
# Set up base paths
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load your dataset
with open(os.path.join(os.path.dirname(__file__), 'cultures.json'), encoding='utf-8') as f:
    dataset = json.load(f)

app = Flask(
    __name__,
    static_folder=os.path.join(base_dir, 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'templates')
)

HUGGING_FACE_API_TOKEN = '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'
app.secret_key = 'cultura_very_secret_key_@2025'

# Chat state memory
chat_state = {
    "awaiting_country": False,
    "detected_topic": None,
    "suggested_cultures": []
}

# --------------------- ROUTES ---------------------

@app.route('/')
def home():
    return render_template('home.html', active_page='home', show_welcome=True)

@app.route('/dashboard')
def dashboard():
    cultures = list(dataset.get("cultures", {}).keys())
    topics = ["motivation", "stress", "balance", "relationships", "joy", "purpose"]
    return render_template('dashboard.html', cultures=cultures, topics=topics, active_page='dashboard', show_welcome=False)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message').strip()

    # USER SELECTED A COUNTRY
    if chat_state["awaiting_country"]:
        country = user_input.strip().title()
        cultures = dataset.get("cultures", {})

        if country in cultures:
            chat_state["awaiting_country"] = False
            data = cultures[country]

            response = f"""🧭 *{country}* draws from the philosophy of **{data['philosophy']}**

🔎 **What it means:**  
{data['philosophy_description']}

🧘 **Daily Habits:**  
- {"\n- ".join(data['habits'])}

📜 **Ancient Wisdom:**  
"{data['ancient_wisdom']}"

💬 **Life Advice:**  
{data['life_advice']}

📖 **Real-life Example:**  
{data['real_life_example']}

💎 **Wisdom Quote:**  
*{data['wisdom_quote']}*
"""
            return jsonify({"reply": response})
        else:
            return jsonify({"reply": f"Sorry, I don’t have data for '{country}'. Please choose another from: {', '.join(chat_state['suggested_cultures'])}"})

    # FIRST TIME INPUT → DETECT TOPIC
    else:
        topics = {
            "motivation": ["lost", "tired", "lazy", "unmotivated"],
            "stress": ["stress", "anxious", "overwhelmed"],
            "balance": ["busy", "work", "overwork"],
            "purpose": ["goal", "meaning", "life"],
            "relationships": ["love", "family", "relationship", "lonely"],
            "joy": ["happy", "sad", "depressed", "joy"]
        }

        detected = "life"
        for topic, words in topics.items():
            for word in words:
                if word in user_input.lower():
                    detected = topic
                    break

        matching = []
        for country, info in dataset["cultures"].items():
            if detected in info.get("cultural_traits", []):
                matching.append(country)

        if not matching:
            matching = list(dataset["cultures"].keys())[:3]

        chat_state["awaiting_country"] = True
        chat_state["detected_topic"] = detected
        chat_state["suggested_cultures"] = matching

        return jsonify({
            "reply": f"It seems you're dealing with *{detected}*. 💭\nWould you like to explore how these cultures handle it?\n\nPlease choose one:\n👉 {', '.join(matching)}"
        })

# --------------------- NAVIGATION PAGES ---------------------

@app.route('/submissions')
def submissions():
    conn = sqlite3.connect('cultura.db')
    c = conn.cursor()
    c.execute('SELECT id, country, problem, solution, advice, timestamp FROM submissions ORDER BY timestamp DESC')
    wisdoms = c.fetchall()
    conn.close()

    favorites = session.get('favorites', [])
    return render_template('submissions.html', wisdoms=wisdoms, active_page='submissions', show_welcome=False)

@app.route('/favorites')
def favorites():
    favorites = session.get('favorites', [])
    wisdoms = []
    if favorites:
        placeholders = ','.join('?' for _ in favorites)
        query = f'SELECT id, country, problem, solution, advice, timestamp FROM submissions WHERE id IN ({placeholders})'

        conn = sqlite3.connect('cultura.db')
        c = conn.cursor()
        c.execute(query, favorites)
        wisdoms = c.fetchall()
        conn.close()

    return render_template('favorites.html', wisdoms=wisdoms, active_page='favorites', show_welcome=False)

@app.route('/feedback')
def feedback():
    return render_template('feedback.html', active_page='feedback', show_welcome=False)

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    name = request.form.get('name')
    feedback = request.form.get('feedback')
    rating = request.form.get('rating')

    conn = sqlite3.connect('cultura.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, feedback TEXT, rating TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    c.execute('INSERT INTO feedback (name, feedback, rating) VALUES (?, ?, ?)', (name, feedback, rating))
    conn.commit()
    conn.close()

    return redirect(url_for('feedback'))


# --------------------- FORM SUBMISSION ---------------------

@app.route('/submit-wisdom', methods=['POST'])
def submit_wisdom():
    country = request.form.get('country')
    problem = request.form.get('problem')
    solution = request.form.get('solution')
    advice = request.form.get('advice')

    conn = sqlite3.connect('cultura.db')
    c = conn.cursor()
    c.execute('INSERT INTO submissions (country, problem, solution, advice) VALUES (?, ?, ?, ?)',
              (country, problem, solution, advice))
    conn.commit()
    conn.close()

    return redirect('/submissions')

@app.route('/wisdom-feed')
def wisdom_feed():
    conn = sqlite3.connect('cultura.db')
    c = conn.cursor()
    c.execute('SELECT country, problem, solution, advice, timestamp FROM submissions ORDER BY timestamp DESC')
    wisdoms = c.fetchall()
    conn.close()
    return render_template('wisdom_feed.html', wisdoms=wisdoms, active_page='feed', show_welcome=False)


def is_valid_username(username):
    return re.match("^[A-Za-z0-9_]{4,20}$", username)

def is_valid_password(password):
    return (len(password) >= 6 and
            re.search("[a-z]", password) and
            re.search("[A-Z]", password) and
            re.search("[0-9]", password))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not is_valid_username(username):
            flash('Username must be 4–20 characters and alphanumeric only.')
            return redirect(url_for('home'))

        if not is_valid_password(password):
            flash('Password must be at least 6 characters with upper, lower, and number.')
            return redirect(url_for('home'))

        conn = sqlite3.connect('cultura.db')
        c = conn.cursor()
        try:
            c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Signup successful! Please login.')
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash('Username already exists.')
        finally:
            conn.close()

    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = sqlite3.connect('cultura.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = username
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie('remember_username', username, max_age=30*24*60*60)  # 30 days
            return resp
        else:
            flash('Invalid credentials.')
            return redirect(url_for('home'))

    return redirect(url_for('home'))

@app.route('/save/<int:id>', methods=['POST'])
def save_favorite(id):
    favorites = session.get('favorites', [])
    if id not in favorites:
        favorites.append(id)
        session['favorites'] = favorites
    return redirect('/submissions')

@app.route('/unsave/<int:id>', methods=['POST'])
def unsave_favorite(id):
    favorites = session.get('favorites', [])
    if id in favorites:
        favorites.remove(id)
        session['favorites'] = favorites

    referrer = request.referrer or '/submissions'
    return redirect(referrer)
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

# --------------------- START APP ---------------------

if __name__ == "__main__":
    app.run(debug=True)
