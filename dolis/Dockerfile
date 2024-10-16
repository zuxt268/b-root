FROM python:3.13.0-alpine

# upgrade pip
RUN pip install --upgrade pip

# get curl for healthchecks
RUN apk add curl
RUN apk add --no-cache tcl tk

RUN adduser -D nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app

WORKDIR /home/app
USER nonroot

COPY --chown=nonroot:nonroot . .

RUN pip install -r requirements.txt

EXPOSE 8003

CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8003"]