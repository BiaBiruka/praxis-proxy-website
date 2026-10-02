FROM ghcr.io/gohugoio/hugo:v0.167.0@sha256:7bb99a126eddeea8fbfaacedc5ef6708805411bdeaa01e668405a137fd02d048

USER root
RUN apk add --no-cache make python3 \
    && mkdir -p /project/node_modules \
    && chmod 1777 /project/node_modules

WORKDIR /project
ENTRYPOINT []
