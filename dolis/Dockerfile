FROM python:3.13

WORKDIR /app

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

RUN adduser -D nonroot
RUN mkdir /app/ && chown -R nonroot:nonroot /app

USER nonroot

COPY --chown=nonroot:nonroot . .

EXPOSE 8003

CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8003"]