# Dockerfile for https://github.com/adnanh/webhook
FROM golang:alpine3.10 AS build

WORKDIR /go/src/github.com/adnanh/webhook

ENV WEBHOOK_VERSION 2.6.9

RUN apk add --update -t build-deps curl libc-dev gcc libgcc

RUN curl -L --silent -o webhook.tar.gz https://github.com/adnanh/webhook/archive/${WEBHOOK_VERSION}.tar.gz && \
    tar -xzf webhook.tar.gz --strip 1 &&  \
    go get -d && \
    go build -o /usr/local/bin/webhook && \
    apk del --purge build-deps && \
    rm -rf /var/cache/apk/* && \
    rm -rf /go

FROM alpine:3.10

RUN apk add curl && \
    rm -rf /var/cache/apk/*

COPY --from=build /usr/local/bin/webhook /usr/local/bin/webhook

VOLUME ["/etc/webhook"]

EXPOSE 9000

ENTRYPOINT ["/usr/local/bin/webhook"]
