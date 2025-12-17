# Step 1: Use a Python image that already has Playwright dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Step 2: Set working directory
WORKDIR /app

# Step 3: Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Copy the rest of the code
COPY . .

# Step 5: Start the bot
CMD ["python", "main.py"]
