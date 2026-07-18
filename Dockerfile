FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DEMO_MODE=true

EXPOSE 7860

CMD ["python", "app.py"]
