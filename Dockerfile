FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads reports

# Set permissions
RUN chmod 777 uploads reports

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
