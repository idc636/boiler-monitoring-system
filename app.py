from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import bcrypt
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

# ---------------- USERS ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,'user')",
                (username, pwd_hash)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except Exception:
            error = "Пользователь уже существует"

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, role FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user[1].encode()):
            session['user_id'] = user[0]
            session['role'] = user[2]
            return redirect(url_for('index'))
        else:
            error = "Неверный логин или пароль"

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- TABLE ----------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM records ORDER BY id")
    records = cur.fetchall()
    conn.close()

    return render_template(
        'index.html',
        records=records,
        is_admin=session.get('role') == 'admin'
    )


@app.route('/update', methods=['POST'])
def update():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    record_id = request.form['id']
    values = request.form.getlist('cell[]')

    conn = get_db()
    cur = conn.cursor()

    for i, val in enumerate(values):
        cur.execute(
            f"UPDATE records SET c{i+1}=%s WHERE id=%s",
            (val, record_id)
        )

    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/add_row', methods=['POST'])
def add_row():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO records DEFAULT VALUES"
    )

    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
