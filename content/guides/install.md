+++
title = "Install and run Praxis"
description = "Choose a verified way to run Praxis and learn what its default server configuration does."
type = "guides"
body_class = "guides-page"
reader_need = "How-to"
topic = "Installation"
+++

Praxis v0.7.2 is the current default documentation release. Its `0.7.2` image tag is available for Linux/amd64; the registry did not confirm an ARM image. The versioned image and digest are below. The source instructions use the matching v0.7.2 release tag.

## Choose how to run it

### Container image

Praxis publishes OCI images to GitHub Container Registry through its release workflow. The verified v0.7.2 Linux/amd64 image is `ghcr.io/praxis-proxy/praxis:0.7.2` with manifest digest `sha256:54267f2c5ea40f1c40e90d6b368e0e080f57bfc58f2e2128396ce3243a569940`. Check the [official Praxis image package](https://github.com/orgs/praxis-proxy/packages/container/package/praxis) for other versions. This verification does not establish an ARM image or the current value of a moving `latest` tag.

The v0.7.2 image runs as the non-root `praxis` user. Its entrypoint starts `praxis -c /etc/praxis/config.yaml`; the bundled config binds the proxy listener to `0.0.0.0:8080`, keeps the admin listener on container loopback at `127.0.0.1:9901`, and returns a static JSON response. It does not route to an upstream until you mount your own config at `/etc/praxis/config.yaml`. Do not append a second `-c` argument to the image command.

Check the pinned v0.7.2 image with:

```console
docker run --rm ghcr.io/praxis-proxy/praxis@sha256:ed6061326911092315e809e901e773e16153d8826086a44b8e95ab715fc78e6b --version
```

That immutable index digest was pulled and its `--version` output was checked. The version tag above is the human-readable reference; the digest pins the exact published image index.

To run the bundled configuration, publish its proxy port:

```console
docker run --rm --publish 8080:8080 ghcr.io/praxis-proxy/praxis@sha256:ed6061326911092315e809e901e773e16153d8826086a44b8e95ab715fc78e6b
```

In another terminal, request the default static response:

```console
curl -i http://127.0.0.1:8080/
```

It returns HTTP `200` with `{"status":"ok","server":"praxis"}`. This response was checked against the published v0.7.2 image. It confirms the container listener is reachable; it does not route to an application service. Stop the container with Ctrl+C. The selected image's default config contains this response and binds the proxy listener to all container interfaces.

For a custom configuration, save a container-specific YAML file with its proxy listener bound to `0.0.0.0:8080`, then mount it read-only at the configured path:

```console
docker run --rm --publish 8080:8080 \
  --volume "$PWD/praxis-container.yaml:/etc/praxis/config.yaml:ro" \
  ghcr.io/praxis-proxy/praxis@sha256:ed6061326911092315e809e901e773e16153d8826086a44b8e95ab715fc78e6b
```

The image entrypoint already passes `-c /etc/praxis/config.yaml`. An upstream address such as `127.0.0.1` refers to the container itself, so configure an address reachable from the container; with Docker's default bridge network, the host backend needs a host-reachable address instead. The read-only mount and existing entrypoint were runtime-checked on Linux with host networking, including config validation and a forwarded request to the host backend. The image health check uses `http://127.0.0.1:9901/healthy` from inside the container; the admin listener is not exposed to the host by the default config. See the [Containerfile at v0.7.2](https://github.com/praxis-proxy/praxis/blob/v0.7.2/Containerfile) and its [container configuration](https://github.com/praxis-proxy/praxis/blob/v0.7.2/examples/configs/operations/container-default.yaml).

### Build the v0.7.2 source

The selected release pins Rust 1.96.0. Install that toolchain, CMake 3.31 or newer, a C/C++ compiler, `pkg-config`, and OpenSSL development headers. The source build does not require the project's optional test, lint, or benchmark tools.

```console
git clone https://github.com/praxis-proxy/praxis.git
cd praxis
git checkout v0.7.2
cargo build --locked --release -p praxis-proxy
./target/release/praxis --version
```

The binary starts with its built-in local configuration on `127.0.0.1:8080` if you do not pass a config file. That default returns a JSON status response; it is a startup check, not a reverse-proxy example. Use `-c path/to/config.yaml` or `--config path/to/config.yaml` to run your own YAML configuration.

For a real forwarded request, follow the [first reverse-proxy tutorial]({{< relref "first-proxy.md" >}}). It uses a local backend and opts in to private endpoints only for that development setup. Continue with [configuration and operations]({{< relref "operate/_index.md" >}}), or {{< docs-link product="praxis" source="docs/developing/getting-started.md" label="see contributor setup" >}} if you plan to change Praxis itself.
