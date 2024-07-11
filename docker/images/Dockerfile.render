# Use an official Python runtime as a parent image, Alpine version for a lighter footprint
FROM python:3.12-slim

# Install necessary packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends mariadb-client \
    && apt-get install -y --no-install-recommends gcc libc-dev python3-dev libffi-dev \
    && apt-get install -y --no-install-recommends curl \
    && apt-get install -y --no-install-recommends bash \
    && apt-get install -y --no-install-recommends openrc \
    && apt-get install -y --no-install-recommends build-essential 

# Clean up
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

# Copy files
COPY app/ ./app
COPY core/ ./core
COPY migrations/ ./migrations

# Copy requirements.txt into the working directory /app
COPY requirements.txt .

# Removes cache at the build stage
RUN find . -type d -name "__pycache__" -exec rm -r {} + && \
    find . -type f -name "*.pyc" -exec rm -f {} +

# Copy entrypoint and set execution permissions
COPY docker/entrypoints/render_entrypoint.sh /app/render_entrypoint.sh
RUN chmod +x /app/render_entrypoint.sh

# Copy the wait-for-db.sh script and set execution permissions
COPY scripts/wait-for-db.sh /app/scripts/wait-for-db.sh
RUN chmod +x /app/scripts/wait-for-db.sh

# Create the .moduleignore file with the module 'webhook' inside
RUN echo "webhook" > /app/.moduleignore

# Update pip
RUN pip install --no-cache-dir --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Expose port 80
EXPOSE 80

# Command to run the application
CMD ["./render_entrypoint.sh"]
