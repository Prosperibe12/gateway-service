ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install os dependencies for our mini vm
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends --no-install-suggests \ 
    build-essential \ 
    && pip install --no-cache-dir --upgrade pip

# Set the working directory to that same code directory
WORKDIR /app

# Copy the requirements file into the container
COPY ./requirements.txt /app

# Install the Python project requirements
RUN pip install --no-cache-dir -r /app/requirements.txt 

# Copy the rest of the code
COPY . /app

# Define the project name
ENV PROJ_NAME=server

# Create a bash script to run the Flask project
# This script will execute at runtime when the container starts 
RUN echo -e "#!/bin/bash\nRUN_PORT=\"\${PORT:-8080}\"\ngunicorn \${PROJ_NAME}:server --bind \"0.0.0.0:\$RUN_PORT\" --workers 2" > ./runner.sh

# Make the bash script executable
RUN chmod +x runner.sh

# Clean up apt cache to reduce image size
RUN apt-get remove --purge -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Expose port 8080
EXPOSE 8080

# Run the Flask project via the runtime script
# when the container starts
CMD ["./runner.sh"]