# Use a slim official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies first (caches requirements install step)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create and switch to a non-root user (improves security)
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Set environment variables for Flask
ENV FLASK_APP=flaskr
ENV FLASK_ENV=production

# Expose port 5000 for the Flask app (default Flask port):contentReference[oaicite:1]{index=1}
EXPOSE 5000

# Run the Flask app (listen on all interfaces)
CMD ["flask", "run", "--host=0.0.0.0"]