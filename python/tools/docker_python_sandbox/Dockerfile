FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 pythonuser

# Install required packages
RUN pip install qrcode pillow flask

# Create workspace directory
RUN mkdir -p /workspace && \
    chown pythonuser:pythonuser /workspace

# Switch to non-root user
USER pythonuser

# Copy server code
COPY server.py /app/server.py

WORKDIR /app
CMD ["python", "server.py"]