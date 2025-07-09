FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY backend/requirements.txt .

# Create Conda environment
RUN conda create -n venv python=3.12 -y && \
    conda install -n venv -c conda-forge gdal geopandas pyogrio -y

# Set environment path so conda env is default
ENV PATH /opt/conda/envs/venv/bin:$PATH

# Install pip packages in conda env
RUN conda run -n venv pip install --no-cache-dir -r requirements.txt

# Copy application code (including subfolders)
COPY backend /app

# Set default Flask app path
ENV FLASK_APP=apppy.py
ENV FLASK_RUN_PORT=5000

# Expose port
EXPOSE 5000

# Start the app using conda env and use Render’s env vars
CMD ["conda", "run", "--no-capture-output", "-n", "venv", "flask", "run", "--host=0.0.0.0"]