FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg tesseract-ocr tesseract-ocr-chi-sim && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY flask_app/ .
RUN mkdir -p uploads logs data/chroma
EXPOSE 8001
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "1", "--threads", "8", "--timeout", "180", "app:app"]
