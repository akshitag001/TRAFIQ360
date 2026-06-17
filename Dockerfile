FROM python:3.10-slim

# Install Chromium and Chromium driver for Selenium headless screenshots
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set working directory
WORKDIR $HOME/app

# Copy requirements and install Python dependencies
COPY --chown=user requirements.txt $HOME/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY --chown=user . $HOME/app/

# Expose the default port used by Hugging Face Spaces
EXPOSE 7860

# Run the Flask server
CMD ["python", "server.py"]
