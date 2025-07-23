# Use the official AWS Lambda base image for Python 3.12
FROM public.ecr.aws/lambda/python:3.12

# Set the working directory
WORKDIR /var/task

# Install system dependencies, including Docker
# Note: Installing Docker inside Docker is complex. This approach installs the Docker CLI
# and relies on the Lambda execution environment having access to a Docker daemon socket.
# For a more robust solution, a custom base image with Docker-in-Docker (DinD) might be required.
RUN yum update -y && \
    yum install -y docker && \
    yum clean all

# Copy configuration files first to leverage Docker caching
COPY .gemini/ ./.gemini/
COPY GEMINI.md ./GEMINI.md

# Copy the application requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install the Gemini CLI
# This assumes gemini-cli is available via pip. Adjust if it's a different installation method.
RUN pip install --no-cache-dir google-gemini-cli

# Copy the FastAPI application code
COPY app/ ./app/

# Set the command for the Lambda function.
# The handler is specified as <module_name>.<handler_function_name>
# In our case, it's app/main.py with the handler object created by Mangum.
CMD ["app.main.handler"]
