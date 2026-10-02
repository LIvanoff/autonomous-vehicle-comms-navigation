FROM ros:noetic-ros-base-focal@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-numpy python3-matplotlib python3-pil python3-yaml \
    ros-noetic-sensor-msgs ros-noetic-rosbag ros-noetic-tf \
    && rm -rf /var/lib/apt/lists/*
ENV MPLBACKEND=Agg PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
WORKDIR /work
CMD ["sleep", "infinity"]
