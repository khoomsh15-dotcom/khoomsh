FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# System dependencies install karna
RUN apt-get update && apt-get install -y \
    libgbm-dev \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Browser ko dependencies ke sath install karna
RUN playwright install --with-deps chromium

CMD ["python", "main.py"]
