# Build an image that can do training and inference in SageMaker
# This is a Python 2 image that uses the nginx, gunicorn, flask stack
# for serving inferences in a stable way.

FROM ubuntu:20.04
MAINTAINER Amazon AI <sage-learner@amazon.com>
ARG AWS_ACCESS_KEY_ID='AKIAUQUCK47AIUYX7O6V'
ARG AWS_SECRET_ACCESS_KEY='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'
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
RUN apt-get -y update && apt-get install -y --no-install-recommends wget nginx ca-certificates && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y python3-pip python3-dev && cd /usr/local/bin && ln -s /usr/bin/python3 /usr/bin/python && pip3 install --upgrade pip
RUN apt-get update
RUN apt-get install -y poppler-utils
RUN apt-get install -y libgl1-mesa-glx
RUN apt-get update && apt-get install -y  tesseract-ocr libtesseract-dev
COPY requirements.txt requirements.txt
COPY fastapi-requirements.txt fastapi-requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install -r fastapi-requirements.txt
RUN pip3 install setuptools==41.0.0 h5py==2.10.0 gunicorn==19.9.0 gevent flask && rm -rf /root/.cache
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"
COPY ./OCR /opt/program
WORKDIR /opt/program
RUN mkdir -p /opt/program/Passport_images/Processed
RUN mkdir -p /opt/program/Pan_images
RUN chmod +x serve
RUN chmod +x /opt/program/predictor.py
RUN chmod +x /opt/program/nginx.conf
RUN chmod +x /opt/program/wsgi.py
RUN chmod +x /opt/program/PP_PN_Read.py
ENTRYPOINT serve
