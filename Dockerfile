FROM python:3.11-slim

ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url "$PIP_INDEX_URL" -r requirements.txt
COPY .env.example .env.deepseek.example .env.qwen.example ./
COPY backend ./backend
COPY teams_bot ./teams_bot
COPY tests ./tests
COPY start-linux.sh ./start-linux.sh

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
