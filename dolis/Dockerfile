FROM python:3.12.7-alpine

# upgrade pip
RUN pip install --upgrade pip

# get curl for healthchecks
RUN apk add curl

RUN apk add --no-cache \
    curl \
    tcl tk \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    make \
    cargo

RUN adduser -D nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app

WORKDIR /home/app
USER nonroot

COPY --chown=nonroot:nonroot . .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install uvicorn

EXPOSE 8003

CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8003"]