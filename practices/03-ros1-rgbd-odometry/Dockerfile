ARG ROS_BASE=ros:noetic-ros-base-focal@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d
FROM ${ROS_BASE}
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-opencv python3-numpy python3-scipy python3-yaml \
    ros-noetic-cv-bridge ros-noetic-message-filters ros-noetic-nav-msgs \
    ros-noetic-rosbag ros-noetic-tf && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
WORKDIR /lab
CMD ["bash"]
