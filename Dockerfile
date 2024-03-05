# Use an official Python runtime as a parent image
FROM python:3.10.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir hyperliquid-python-sdk discord_webhook

# Run the script when the container launches
CMD ["python", "./main.py"]
