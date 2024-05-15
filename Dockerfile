FROM ubuntu:noble

RUN apt-get update -y && apt-get install -y build-essential

RUN git clone git@github.com:python/cpython.git && \
    cd cpython && \
    ./configure --disable-gil && \
    make && make install


COPY . /app
WORKDIR /app

ENTRYPOINT python microweb.py flask_app_real:app
