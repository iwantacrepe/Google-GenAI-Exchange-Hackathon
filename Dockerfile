# ============================================
# 🐳 LEGAL DEMYSTIFIER — Local Build Version
# ============================================

# Base image
FROM python:3.11-slim

# Install system dependencies (for PyMuPDF, pdfminer, etc.)
RUN apt-get update && apt-get install -y \
    build-essential libpoppler-cpp-dev poppler-utils libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy local project into the container (includes .env, templates, etc.)
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Load environment variables (uncomment if needed)
# ENV GOOGLE_API_KEY=your_key_here \
#     NEO4J_URI=neo4j+s://47094088.databases.neo4j.io \
#     NEO4J_USERNAME=neo4j \
#     NEO4J_PASSWORD=your_password \
#     NEO4J_DATABASE=neo4j
HEALTHCHECK CMD curl -f http://localhost:80/healthz || exit 1

# Set Python env vars
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=80

# Expose port
EXPOSE 80

# Start the app using Gunicorn with config file
CMD ["gunicorn", "-c", "gunicorn.conf.py", "--bind", "0.0.0.0:80", "app:app"]
# ============================================