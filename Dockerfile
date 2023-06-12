# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY ./data/* /app/data/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Expose the port that the Gradio app will run on
EXPOSE 7860

# Run the command to start the Gradio app
CMD ["python", "chat_web.py"]
