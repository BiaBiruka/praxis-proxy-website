+++
title = "Praxis Grid"
description = "Discover Grid through its official repository and its original unversioned guide."
type = "guides"
body_class = "guides-page"
+++

Grid is a related external project, not a fourth release catalog entry on this site. It describes itself as a distributed control plane for inference backends: Grid writes routing state for Praxis AI, while gateways handle request traffic.

Start with the [official Grid repository and current README](https://github.com/praxis-proxy/grid). The repository's default branch is not pinned to a release by this site; check its own tags and documentation before deploying it. Its current README describes `noMetrics` as the general provider strategy and `queueDepth` or `kvCachePressure` for llm-d pools. Do not apply older diagrams or routing examples without checking them against the current Grid source.

The [original Grid overview](https://praxis.fast/docs/grid/overview/) and [original Grid visual guide](https://praxis.fast/praxis-grid-booklet.html) remain available as unversioned historical resources. They are not the current versioned documentation here, and portions of their routing/scoring description differ from the current repository. Grid uses its own Apache-2.0 license; this site's Praxis, AI, and Policy releases remain separate projects.
