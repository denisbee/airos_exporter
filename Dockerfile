FROM python:3.9-alpine
ENV APK_DEP="libressl libev"
ENV APK_BUILD_DEP="gcc git libev-dev musl-dev libffi-dev libressl-dev make rust cargo"
ADD requirements.txt /srv/service/
WORKDIR /srv/service
RUN set -x && apk add --no-cache ${APK_BUILD_DEP} ${APK_DEP} && \
    pip install -r requirements.txt && \
    apk del --no-cache ${APK_BUILD_DEP} && apk add --no-cache ${APK_DEP}
USER 1000
ADD airos_exporter.py /srv/service/
ENTRYPOINT ["python3", "-u", "airos_exporter.py" ]
