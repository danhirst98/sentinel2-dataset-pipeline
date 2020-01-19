# Run the pipeline in a docker container to make installation easier.
#
# in theory for windows:
#
# docker run \
# -e S3_ACCESS_KEY=<Access key here> \
# -e S3_SECRET_KEY=<Secret key here> \
# -v C:\data\working\:/working \
# -v C:\data\working\input:/targets \
# s1-ard-pypeline:latest \
# batch_run.py -input iipcom/download -output iipcom/wil_test -targets /targets/batch.csv

FROM python:3.7
LABEL maintainer="Wil Selwood <wil.selwood@sa.catapult.org.uk>"

WORKDIR /app/
ENV DIRS_WORKING=/working DIRS_DOWNLOAD=/working DIRS_OUTPUT=/working/output SNAP_PATH=/app/snap

COPY dist/s1_ard_pypeline-0.1.0-py2.py3-none-any.whl ./
COPY snap/install_snap.sh ./
COPY config.cfg ./
ADD graphs graphs/

# run everything at once to avoid too many intermediate containers.
RUN apt-get update \
    && apt-get install -y gcc gdal-bin python-gdal unzip zip wget \
    && pip install --upgrade pip setuptools wheel \
    && pip install s1_ard_pypeline-0.1.0-py2.py3-none-any.whl \
    && rm ./s1_ard_pypeline-0.1.0-py2.py3-none-any.whl \
    && chmod 755 ./install_snap.sh \
    && ./install_snap.sh \
    && rm ./install_snap.sh \
    && apt-get remove --purge -y gcc wget \
    && apt-get clean

# Drop snap config over the top of the installed values.
COPY snap/bin/gpt.vmoptions /app/snap/bin/
COPY snap/etc/snap.auxdata.properties /app/snap/etc/
