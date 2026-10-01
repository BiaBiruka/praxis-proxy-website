+++
title = "Praxis"
description = "A configurable HTTP reverse proxy and TCP forwarder, with a Rust framework for custom filters."
type = "landing"
layout = "list"
product = "praxis"
body_class = "product-overview-page"
+++

Run Praxis as an HTTP reverse proxy or TCP forwarder. Configure routing, load balancing, TLS, and built-in filters in YAML; you do not need to write Rust for those tasks. Start with the [installation choices]({{< relref "guides/install.md" >}}) and the [first reverse-proxy tutorial]({{< relref "guides/first-proxy.md" >}}), or {{< docs-link product="praxis" source="docs/quickstart.md" label="read the release quickstart" >}}.

Praxis v0.7.2 is pre-v1 software. Its [security policy](https://github.com/praxis-proxy/praxis/blob/v0.7.2/SECURITY.md) marks every 0.x release unsupported. Review the [release-scoped capability matrix]({{< relref "capabilities.md" >}}) before choosing features. For custom behavior, use the separate [Rust extension path]({{< relref "../guides/extend/_index.md" >}}).

{{< product-landing product="praxis" >}}
