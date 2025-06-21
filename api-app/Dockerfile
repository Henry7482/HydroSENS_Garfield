# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

ENV PYTHONPATH=/app


# Install system dependencies (for shapefile processing if needed later)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Insall latexmk for Latex report generation
RUN apt-get update && apt-get install -y \
    latexmk \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-latex-recommended \
    texlive-xetex \
    texlive-science \
    ghostscript \
    && apt-get clean
    
# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run the app
CMD ["flask", "--app", "app.py", "run", "--host=0.0.0.0", "--port=5050"]
