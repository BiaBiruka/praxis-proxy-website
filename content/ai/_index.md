+++
title = "Praxis AI"
description = "An alpha AI gateway with provider-aware routing and filters, built on the Praxis proxy runtime."
type = "landing"
layout = "list"
product = "ai"
body_class = "product-overview-page"
+++

Praxis AI adds AI-specific request classification, provider routing, translation, and agent-protocol features to the Praxis proxy runtime. It is a separate build and release from the core proxy. The selected v0.4.1 release is alpha; its [security policy](https://github.com/praxis-proxy/ai/blob/v0.4.1/SECURITY.md) supports the 0.4.x line as alpha.

The release quickstart is a source-build guide. Its OpenAI example needs a valid `OPENAI_API_KEY`, network access to `api.openai.com:443`, and a provider account; the example request uses `gpt-4o`. Set the key in your shell before sending that request. {{< docs-link product="ai" source="docs/quickstart.md" label="Run the AI gateway quickstart" >}}. For capabilities and setup-dependent features, {{< docs-link product="ai" source="docs/features.md" label="read the release feature overview" >}}.

The AI release and Praxis release numbers are independent. AI v0.4.1's manifest depends on Praxis crates v0.7.0, while this site's core default is v0.7.2; the site has not verified that pair as a compatibility set. Choose versions from the relevant project manifests and test the combination you deploy.

{{< product-landing product="ai" >}}
