FROM python:3.12-slim

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use Cloud Run PORT env variable (default 8080)
ENV PORT 8080
CMD exec gunicorn --bind 0.0.0.0:${PORT} main:app
