# Microsoft ki official image jisme saari libraries pehle se hain
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Browser ko dependencies ke saath force install karna
RUN playwright install --with-deps chromium

CMD ["python", "main.py"]
