FROM ollama/ollama:latest

# Set the working directory inside the container
WORKDIR /app

# Install Python, venv, and pip so the container can run the Python app
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip grep && rm -rf /var/lib/apt/lists/*

#Configure Ollama to listen on all interfaces
ENV OLLAMA_HOST=0.0.0.0:11434

# Copy dependency file and install Python packages into a virtual environment
COPY requirements.txt ./
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the full application into the container
COPY . /app

# Expose the Ollama API port
EXPOSE 11434

# Use the virtual environment for Python, start Ollama in the background,
# pull the llama3 model, then run the app.
ENV PATH="/opt/venv/bin:${PATH}"
ENTRYPOINT []

# Start Ollama, then only pull the model if it's not already present, then
# run the Python app.
CMD ["bash", "-c", "ollama serve > /dev/null 2>&1 & until ollama list >/dev/null 2>&1; do echo 'Waiting for Ollama to start...'; sleep 1; done; if ! ollama list | grep -q '^llama3'; then echo 'Pulling llama3 model...'; ollama pull llama3 >/dev/null 2>&1 || true; fi; echo 'Starting application...'; python main.py"]