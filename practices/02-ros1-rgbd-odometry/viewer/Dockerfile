FROM python:3.11-slim
RUN pip install --no-cache-dir rerun-sdk==0.23.4 numpy==2.2.6 pillow==11.3.0
WORKDIR /lab
CMD ["python", "viewer/show.py", "output/attempt01", "--serve"]
