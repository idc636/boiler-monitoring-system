@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # проверяем роль
    cur.execute("SELECT role FROM users WHERE id = %s", (session["user_id"],))
    role = cur.fetchone()[0]

    if role != "admin":
        cur.close()
        conn.close()
        return "Forbidden", 403

    # создаём пустую строку (37 колонок)
    cur.execute("""
        INSERT INTO records (
            c1, c2, c3, c4, c5,
            c6, c7, c8, c9, c10,
            c11, c12, c13, c14, c15,
            c16, c17, c18, c19, c20,
            c21, c22, c23, c24, c25,
            c26, c27, c28, c29, c30,
            c31, c32, c33, c34, c35,
            c36, c37
        ) VALUES (
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '', '', '',
            '', ''
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))
