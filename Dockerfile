# Build Environment: Playwright
FROM mcr.microsoft.com/playwright/python:v1.41.2-jammy

# Create a working directory in the Docker image
WORKDIR /app

# Copy the contents of the src/ directory into the Docker image
COPY src/ .

# Install Python dependencies from requirements.txt
RUN python -m pip install -r requirements.txt

# Expose the port that Hypercorn will listen on
EXPOSE $PORT

# Command to run the application using Hypercorn
CMD ["sh", "-c", "hypercorn -b 0.0.0.0:$PORT app:app"]
