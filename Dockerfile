# Use the official Python 3.11 image
FROM python:3.11-slim

# Install system dependencies including gdal and g++
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        g++ \
        wget \
        ca-certificates \
        tk-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install the GDAL Python bindings (should match the GDAL version installed on system)
# RUN pip install gdal==3.6.2

# Set the working directory
WORKDIR /app

# Copy app files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add credentials for CDS API
RUN touch /root/.cdsapirc && \
    echo "url: https://cds.climate.copernicus.eu/api" >> /root/.cdsapirc && \
    echo "key: a9aa725d-6aeb-4b3e-b163-6466b4024a5f" >> /root/.cdsapirc

# Run the main Python script
CMD ["python", "main_sentinel_update.py"]
