import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

DATABASE_URL = os.environ.get("DATABASE_URL")


# -------------------- DB INIT --------------------

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id SERIAL PRIMARY KEY,
        c1 TEXT, c2 TEXT, c3 TEXT, c4 TEXT, c5 TEXT,
        c6 TEXT, c7 TEXT, c8 TEXT, c9 TEXT, c10 TEXT,
        c11 TEXT, c12 TEXT, c13 TEXT, c14 TEXT, c15 TEXT,
        c16 TEXT, c17 TEXT, c18 TEXT, c19 TEXT, c20 TEXT,
        c21 TEXT, c22 TEXT, c23 TEXT, c24 TEXT, c25 TEXT,
        c26 TEXT, c27 TEXT, c28 TEXT, c29 TEXT, c30 TEXT,
        c31 TEXT, c32 TEXT, c33 TEXT, c34 TEXT, c35 TEXT,
        c36 TEXT, c37 TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()

# -------------------- AUTH --------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "user")

        conn = get_conn()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, generate_password_hash(password), role)
            )
            conn.commit()
            return redirect(url_for("login"))
        except Exception:
            conn.rollback()
            error = "Пользователь уже существует"
        finally:
            cur.close()
            conn.close()

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash, role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["role"] = user[2]
            return redirect(url_for("index"))
        else:
            error = "Неверный логин или пароль"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------- MAIN TABLE --------------------

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM records ORDER BY id")
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "index.html",
        records=records,
        is_admin=(session.get("role") == "admin")
    )


@app.route("/add", methods=["POST"])
def add_record():
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    values = [request.form.get(f"c{i}") for i in range(1, 38)]

    conn = get_conn()
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * 37)
    columns = ",".join([f"c{i}" for i in range(1, 38)])

    cur.execute(
        f"INSERT INTO records ({columns}) VALUES ({placeholders})",
        values
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))


# --------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
