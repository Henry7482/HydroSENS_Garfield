# Use the official Python 3.11 image
FROM python:3.11-slim

# Install system dependencies
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

# Set the working directory
WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install wheel 'setuptools>=67'

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir --force-reinstall 'GDAL[numpy]==3.6.2'

# Copy app files into the container
COPY . .

# Add credentials for CDS API
RUN touch /root/.cdsapirc && \
    echo "url: https://cds.climate.copernicus.eu/api" >> /root/.cdsapirc && \
    echo "key: a9aa725d-6aeb-4b3e-b163-6466b4024a5f" >> /root/.cdsapirc

# Run the main Python script
CMD ["python", "app.py"]
