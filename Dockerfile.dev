# Use an official Python runtime as a parent image
FROM python:3.11-alpine

# Set the working directory in the container to /app
WORKDIR /app

# Copy the contents of the local app/ directory to the /app directory in the container
COPY app/ ./app

# Copy requirements.txt at the /app working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Update pip
RUN pip install --no-cache-dir --upgrade pip

# Expose port 5000
EXPOSE 5000

# Run the application
CMD flask db upgrade && flask run --host=0.0.0.0 --port=5000 --reload --debug

