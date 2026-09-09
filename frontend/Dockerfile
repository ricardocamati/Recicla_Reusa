FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1/')"

CMD ["python", "-m", "http.server", "80", "--bind", "0.0.0.0", "--directory", "/app"]
