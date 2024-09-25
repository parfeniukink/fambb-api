FROM python:3.12.6-slim as base

# Configure Python
ENV PYTHONUNBUFFERED=1

# Configure uvicorn
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
ENV UVICORN_RELOAD=true

# Install basic dependencies
RUN apt-get update \
    # dependencies for building Python packages && cleaning up unused files
    && apt-get install -y build-essential \
    libcurl4-openssl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip install --upgrade pip

WORKDIR /app/
COPY ./ ./



# Dev image
from base as dev

RUN pip install -r requirements/dev.txt
EXPOSE $UVICORN_PORT
ENTRYPOINT ["python"]
CMD ["-m", "uvicorn", "src.main:app"]



# Production image
from base as prod

RUN pip install -r requirements/main.txt
EXPOSE $UVICORN_PORT
ENTRYPOINT ["python"]
CMD ["-m", "uvicorn", "src.main:app"]

