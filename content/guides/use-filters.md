+++
title = "Choose and configure filters"
description = "Use Praxis’s built-in filters to change how a proxy handles requests."
body_class = "guides-page"
reader_need = "How-to"
topic = "Configuration"
+++

Praxis applies filters to requests as they pass through a proxy. A filter is a named rule that can forward a request, change a header, or return a response. You choose and configure built-in filters in a YAML file; this does not require writing Rust.

Each Praxis documentation link below shows the current default release. Use a binary built from that same Praxis release; {{< docs-link product="praxis" source="docs/quickstart.md" label="the quickstart" >}} explains how to build and run it.

## Choose a filter

Start with the behavior you need:

- Return a fixed response, for example for a simple status page: use `static_response`.
- Send requests to an application service: use `router` to match the request path and `load_balancer` to choose a service address.
- Add or change request or response headers: use `headers`.
- Apply security checks, rate limits, or logging: choose a matching filter in {{< docs-link product="praxis" source="docs/filters/reference.md" label="the filter reference" >}}.

A **backend** is the application service that receives a proxied request. A **route** is a rule that matches a request and selects a named group of backend addresses. {{< docs-link product="praxis" source="docs/operating/configuration.md" label="The configuration guide" >}} shows how routers and load balancers work together.

## Try a complete configuration

You need a Praxis source checkout, Rust/Cargo, Make, and `curl`. If you already have a matching Praxis binary, skip `make release` and use its path in the commands below.

This local example returns a response directly, without contacting a backend. Save it as `praxis.yaml`:

```yaml
listeners:
  - name: local
    address: "127.0.0.1:8080"
    filter_chains: [main]

filter_chains:
  - name: main
    filters:
      - filter: static_response
        status: 200
        body: "Filter configuration is active."
        headers:
          - name: "X-Praxis-Filter"
            value: "configured"
```

`listeners` sets the local address that accepts requests. The filter chain is the ordered list of rules for that listener. Here, `static_response` replies with status `200`, the message, and the `X-Praxis-Filter` header.

From the Praxis source checkout for the release shown in the links above, build and check the config:

```console
make release
./target/release/praxis --validate --config praxis.yaml
```

Successful validation exits with status `0` and does not start the proxy. Then start it in one terminal:

```console
./target/release/praxis -c praxis.yaml
```

In another terminal, send a request:

```console
curl -i http://127.0.0.1:8080/
```

The response should have status `200`, include `X-Praxis-Filter: configured`, and contain `Filter configuration is active.` No separate backend is needed for this example.

This listener is bound to the local machine. To forward requests to a real service instead, configure a `router` and `load_balancer` with that service’s address. Praxis blocks loopback, private-network, and link-local upstream addresses by default; the {{< docs-link product="praxis" source="docs/quickstart.md" label="quickstart" >}} explains the local-development opt-in and its security implications.

## Apply changes safely

Praxis reloads supported filter and routing changes while it runs. If the new configuration is invalid, it logs an error and continues with the last valid configuration. Some settings, including listener addresses, require a restart. Reloading resets the state of rate limiters and circuit breakers. See {{< docs-link product="praxis" source="docs/operating/configuration.md" label="the configuration guide" >}} for the full list.

## When a built-in filter is not enough

If the behavior you need is missing from the reference, it requires custom Rust code and a Praxis build that includes the filter. Developers can follow {{< docs-link product="praxis" source="docs/filters/http-filter-tutorial.md" label="the HTTP filter tutorial" >}} to add a custom filter to their proxy. To contribute a new built-in filter to Praxis itself, use {{< docs-link product="praxis" source="docs/developing/adding-filters.md" label="the built-in filter development guide" >}}.
