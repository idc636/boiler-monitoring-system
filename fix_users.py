import psycopg2
from werkzeug.security import generate_password_hash
import os

# 1. Подключение к БД (возьми URI из Railway или .env)
DB_URI = os.getenv("DATABASE_URL") or "postgresql://user:pass@host:port/dbname"

conn = psycopg2.connect(DB_URI)
cur = conn.cursor()

# 2. Удаляем сломанных пользователей
cur.execute("DELETE FROM users WHERE username IN ('admin1', 'user1', 'user2', 'user3', 'operator')")

# 3. Хешируем существующего admin (введи его текущий пароль вручную)
admin_plain = input("Введите ТЕКУЩИЙ пароль для admin: ")
admin_hashed = generate_password_hash(admin_plain)
cur.execute("UPDATE users SET password = %s WHERE username = %s", (admin_hashed, 'admin'))

# 4. Создаём тестовых пользователей с правильными ролями
new_users = [
    ('admin1', generate_password_hash('admin123'), 'admin'),
    ('operator1', generate_password_hash('oper123'), 'operator'),
    ('operator2', generate_password_hash('oper123'), 'operator')
]
cur.executemany("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", new_users)

conn.commit()
print("✅ Готово: пароли захэшированы, пользователи пересозданы.")
cur.close()
conn.close()
