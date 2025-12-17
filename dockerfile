# Microsoft ki official image jisme Playwright dependencies pehle se hain
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

# Requirements install karna
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pura code copy karna
COPY . .

# Browser aur uski dependencies ko final touch dena
RUN playwright install --with-deps chromium

# Bot start karne ki command
CMD ["python", "main.py"]
