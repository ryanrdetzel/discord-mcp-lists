FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server1.py .

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["python", "server1.py"]
