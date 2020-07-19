FROM python:3.8-alpine3.12
ADD requirements.txt airos_exporter.py /srv/service/
WORKDIR /srv/service
RUN apk add --no-cache gcc git libev-dev musl-dev libffi-dev libressl-dev make libressl libev && \
    pip install -r requirements.txt && \
    apk del --no-cache git gcc libev-dev musl-dev libffi-dev libressl-dev make
USER 1000
ENTRYPOINT ["python3", "-u", "airos_exporter.py" ]
