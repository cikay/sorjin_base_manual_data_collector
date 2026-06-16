# syntax=docker/dockerfile:1

# ---- Builder: compile deps (fasttext, lxml) and install into site-packages ----
FROM python:3.10-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# build-essential is needed to compile the fasttext C++ extension
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv

WORKDIR /app
COPY Pipfile Pipfile.lock ./

# Install the exact locked dependency set into the image's system site-packages
# so the runtime stage can copy them without the build toolchain.
RUN pipenv sync --system


# ---- Runtime: slim image with only what's needed to run the crawler ----
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/hf-cache

# libgomp1 is the OpenMP runtime that the compiled fasttext extension links against
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Pull in the installed packages and their console scripts from the builder.
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
COPY . .

# lang_model.py fetches the GlotLID model from HuggingFace at import time. It is
# downloaded on first run into HF_HOME (/hf-cache) and reused afterwards; mount a
# volume there so it's fetched only once. Set HF_TOKEN for a faster, authenticated
# download (passed at run time via --env-file / env_file).
#
# Crawl output and logs go to /data, the model cache to /hf-cache — mount volumes
# on both so results and the downloaded model persist across runs.
VOLUME ["/data", "/hf-cache"]

ENTRYPOINT ["python", "main.py"]
CMD ["--output", "/data/output.csv", "--log-file", "/data/logs/crawler.log"]
