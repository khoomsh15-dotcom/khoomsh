FROM mcr.microsoft.com/playwright/python:v1.49.0-noble
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Ye line browser aur uski saari dependencies install karegi
RUN playwright install --with-deps chromium
CMD ["python", "main.py"]
