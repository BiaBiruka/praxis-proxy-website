FROM ghcr.io/gohugoio/hugo:v0.164.0@sha256:f8671f2299e60154536c158bff8ce27f6eef4dddbbfc73bcce66263276ae0f80

USER root
RUN apk add --no-cache make python3 \
    && mkdir -p /project/node_modules \
    && chmod 1777 /project/node_modules

WORKDIR /project
ENTRYPOINT []
