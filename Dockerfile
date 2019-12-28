FROM alpine:3.10.3
MAINTAINER Abe Hoffman "abrahamrhoffman@gmail.com"

RUN echo "http://ftp.acc.umu.se/mirror/alpinelinux.org/v3.10/community" \
    >> /etc/apk/repositories
RUN apk update
RUN apk upgrade --no-cache
RUN apk add --no-cache python3-dev
RUN apk add --no-cache build-base
RUN apk add --no-cache python3
RUN apk add --no-cache bash
RUN apk add --no-cache musl
RUN apk add --no-cache git
RUN apk add --no-cache --upgrade bash
RUN apk add --no-cache qemu-img
RUN apk add --no-cache qemu-system-x86_64
RUN apk add --no-cache libvirt-daemon
RUN apk add --no-cache py-libvirt
RUN apk add --no-cache py-libxml2
RUN apk add --no-cache virt-install
RUN apk add --no-cache openrc

RUN cd /usr/bin && \
    ln -sf python3 python \
    ln -sf pip3 pip

RUN pip install gevent
RUN pip install cython
RUN pip install --no-binary :all: falcon

RUN rm -rf /var/cache/*
RUN rm -rf /root/.cache/*

RUN rc-update add libvirtd
RUN rc-service libvirtd start

COPY archangel/src /x/src
COPY archangel/qemu /x/qemu
RUN chmod 0775 /x/src/scripts/run.sh

CMD ["bash", "/x/src/scripts/run.sh"]