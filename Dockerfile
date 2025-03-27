FROM python:3.12.6-slim as base

# configure python
ENV PYTHONUNBUFFERED=1

# install basic dependencies
RUN apt-get update \
    # dependencies for building Python packages && cleaning up unused files
    && apt-get install -y build-essential \
    libcurl4-openssl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# python dependencies
RUN pip install --upgrade pip

WORKDIR /app/
COPY ./ ./


# DEV IMAGE
from base as dev

ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
ENV UVICORN_RELOAD=true

RUN pip install -r requirements/dev.txt
EXPOSE $UVICORN_PORT
ENTRYPOINT ["python"]
CMD ["-m", "uvicorn", "src.main:app"]



# PRODUCTION IMAGE
from base as prod

RUN pip install -r requirements/main.txt
EXPOSE 8000
ENTRYPOINT ["gunicorn"]
CMD ["--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "src.main:app"]
