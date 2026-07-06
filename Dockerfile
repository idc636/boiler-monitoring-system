FROM python:3.11-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт
EXPOSE 10000

# Команда запуска
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
