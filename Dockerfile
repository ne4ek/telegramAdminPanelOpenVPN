FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только необходимые пакеты
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Делаем скрипты исполняемыми
RUN chmod +x add_user.sh

