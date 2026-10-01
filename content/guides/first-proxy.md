+++
title = "Run your first reverse proxy"
description = "Build Praxis, configure one local upstream, and verify that a real request reaches it."
type = "guides"
body_class = "guides-page"
reader_need = "Tutorial"
topic = "First run"
+++

This tutorial builds Praxis v0.7.2, starts a tiny HTTP backend, then forwards a request through Praxis to that backend. You will configure the proxy in YAML; no Rust filter code is needed.

You need the Rust 1.96.0 toolchain pinned by this release, Cargo, CMake 3.31 or newer, a C/C++ compiler, `pkg-config`, OpenSSL development headers, Python 3, and `curl`. See the [installation guide]({{< relref "install.md" >}}) for the source-build prerequisites and container notes.

## Build Praxis

From a terminal, check out the selected release and build only the proxy binary:

```console
git clone https://github.com/praxis-proxy/praxis.git
cd praxis
git checkout v0.7.2
cargo build --locked -p praxis-proxy
```

This builds the local debug binary for a quicker first run. For a release-mode binary, build with `cargo build --locked --release -p praxis-proxy` and use `./target/release/praxis` in the commands below.

## Start a small backend

In a second terminal on the same machine, create a response and serve it on port 3000:

```console
mkdir -p /tmp/praxis-demo-backend
printf 'hello from backend\n' > /tmp/praxis-demo-backend/index.html
python3 -m http.server 3000 --bind 127.0.0.1 --directory /tmp/praxis-demo-backend
```

Leave that command running. In another terminal, confirm the backend directly:

```console
curl http://127.0.0.1:3000/
```

The response body should be `hello from backend`.

## Configure the proxy

From the Praxis source checkout, save this as `praxis.yaml`:

```yaml
insecure_options:
  allow_private_endpoints: true

listeners:
  - name: web
    address: "127.0.0.1:8080"
    filter_chains: [main]

filter_chains:
  - name: main
    filters:
      - filter: router
        routes:
          - path_prefix: "/"
            cluster: backend
      - filter: load_balancer
        clusters:
          - name: backend
            endpoints:
              - "127.0.0.1:3000"
```

`router` matches the request path and chooses the named `backend` cluster. `load_balancer` selects an endpoint from that cluster. Praxis blocks loopback upstreams by default; `allow_private_endpoints` is required here because the backend is on the same machine. This opt-in is for this local tutorial, not a production setting.

## Validate, start, and send a request

Validate the file before starting the listener:

```console
./target/debug/praxis --validate --config praxis.yaml
```

If validation exits successfully, start Praxis:

```console
./target/debug/praxis --config praxis.yaml
```

From a third terminal, send a request through the proxy:

```console
curl -i http://127.0.0.1:8080/
```

You should receive HTTP status `200` and the body `hello from backend`. The backend terminal should log a `GET /` request. This confirms that the request reached the configured upstream through Praxis.

Stop both servers with Ctrl+C. Remove the temporary backend directory if you no longer need it:

```console
rm -rf /tmp/praxis-demo-backend
```

Next, [choose and configure built-in filters]({{< relref "use-filters.md" >}}), browse the [versioned configuration examples]({{< relref "../examples/_index.md" >}}), or continue to [operator tasks]({{< relref "operate/_index.md" >}}). For exact filter fields, {{< docs-link product="praxis" source="docs/filters/reference.md" label="use the v0.7.2 filter reference" >}}.
