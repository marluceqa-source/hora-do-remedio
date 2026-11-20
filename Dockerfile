# Hora do Remédio — imagem única usada pelos serviços api, bot e migrate (ver docker-compose.yml)
FROM python:3.12-slim

# tesseract-ocr(-por): OCR local (RF03). espeak: voz de fallback do pyttsx3 no Linux (RF01/RF06).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-por \
        espeak \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p database logs assets/uploads

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
