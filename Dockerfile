FROM python:3.10-slim-buster

RUN apt update && apt upgrade -y
RUN apt-get install build-essential python3-dev -y
# Set the working directory
WORKDIR /app

# Copy the required files
COPY requirements.txt .
COPY . /app

# Install the dependencies
RUN pip install -r requirements.txt

# Run the application
CMD ["python", "bot.py"]
