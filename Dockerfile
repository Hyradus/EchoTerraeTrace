# Use the official miniconda image from Docker Hub
FROM continuumio/miniconda3

# Set the working directory
WORKDIR /app

# Install dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libegl1-mesa \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    ffmpeg \
    libsm6 \
    libxext6 \
    libopengl0

# Copy the environment.yml file into the Docker image
COPY environment.yml .

# Create the conda environment
RUN conda env create -f environment.yml

# Activate the environment and ensure it's available in the PATH
RUN echo "conda activate ett" >> ~/.bashrc
ENV PATH=/opt/conda/envs/ett/bin:$PATH

# Copy your Bokeh application code into the Docker image
COPY ./app /app
COPY ./Notebooks /Notebooks

# Expose the port that Bokeh server will run on
EXPOSE 5006
EXPOSE 5007
EXPOSE 5008
EXPOSE 8888

# Make the script executable
RUN chmod +x /app/start.sh

# Update the CMD to run the script
CMD ["/app/start.sh"]
