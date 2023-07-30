FROM ubuntu:20.04

# Set the working directory in the container to /app
WORKDIR /app

# Install wget and download Miniconda
RUN apt-get update && apt-get install -y libx11-6 &&  \
    apt-get install -y wget && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.8.2-Linux-x86_64.sh && \
    bash Miniconda3-py38_4.8.2-Linux-x86_64.sh -b -p /miniconda3 && \
    rm Miniconda3-py38_4.8.2-Linux-x86_64.sh

# Create a new conda environment and install packages
RUN /miniconda3/bin/conda create -n aeya python=3.9 flask gunicorn matplotlib pip -y && \
    /miniconda3/envs/aeya/bin/pip  install opencv-python-headless gmic

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 1515 available to the world outside this container
EXPOSE 1515

# Run app.py when the container launches
CMD ["/miniconda3/envs/aeya/bin/gunicorn", "-w", "4", "-b", "0.0.0.0:1515", "--timeout", "300", "--log-level", "info", "aeya_server:app"]

