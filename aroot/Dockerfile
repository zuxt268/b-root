FROM python:3.12.7-alpine

# upgrade pip
RUN pip install --upgrade pip

# install curl and tk-related tools (already present)
RUN apk add --no-cache curl tcl tk

# install build tools for psutil and other native extensions
RUN apk add --no-cache gcc python3-dev musl-dev linux-headers

# permissions and nonroot user for tightened security
RUN adduser -D nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app
RUN mkdir -p /var/log/flask-app && touch /var/log/flask-app/flask-app.err.log && touch /var/log/flask-app/flask-app.out.log
RUN chown -R nonroot:nonroot /var/log/flask-app
WORKDIR /home/app
USER nonroot

# copy all the files to the container
COPY --chown=nonroot:nonroot . .

# venv
ENV VIRTUAL_ENV=/home/app/venv

# python setup
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install -r requirements.txt

# define the port number the container should expose
EXPOSE 8000

ENV FLASK_APP=aroot
ENV FLASK_ENV=production

CMD ["python", "app.py"]
