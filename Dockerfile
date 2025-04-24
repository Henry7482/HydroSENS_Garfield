# Use the official Python 3.11 image
FROM python:3.11-slim

# Install FFMPEG and dependencies needed for Conda and GDAL
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    bzip2 \
    ca-certificates \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libxrender1 \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p $CONDA_DIR && \
    rm /miniconda.sh
ENV PATH=$CONDA_DIR/bin:$PATH

# Install GDAL via conda
RUN conda install -y -c conda-forge gdal && conda clean -afy

# Set the working directory
WORKDIR /app

# Copy app files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN touch /root/.cdsapirc && \
    echo "url: https://cds.climate.copernicus.eu/api" >> /root/.cdsapirc && \
    echo "key: a9aa725d-6aeb-4b3e-b163-6466b4024a5f" >> /root/.cdsapirc


# Run the main Python script
CMD ["python", "main_sentinel_update.py"]
