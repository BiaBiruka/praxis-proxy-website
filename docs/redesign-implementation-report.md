# Website redesign implementation and validation

A subsequent user-requested skill-guided revision changes the visual tokens, type scale, and end-user onboarding. See [skill-guided-revision.md](skill-guided-revision.md) for the current implementation and evidence; the measurements below describe the first pass.

Date: 2026-09-30. The four implementation phases and validation are complete. The approved reference is [ui-ux-redesign-plan.md](ui-ux-redesign-plan.md).

## Implementation

Three supervised GPT-6-luna agents, all using medium effort, implemented the visual/site, documentation, and search/diagram work. Root reviewed their changes, requested revisions, integrated shared configuration, and ran the checks.

| Phase | Delivered |
| --- | --- |
| Foundations | Charcoal/green light and dark palettes, SVG product identity, self-hosted IBM Plex with OFL and provenance, source-path Diátaxis metadata |
| Orientation | Homepage hero and ecosystem diagram, task choices, product comparison rows, `/start/`, `/docs/`, product overviews, Community, responsive navigation/footer, helpful 404 |
| Reading/discovery | Current-version grouped sidebar, one article H1, retained anchors, summaries, related documents, exact source actions, counterpart-aware version switching, mobile TOC, scoped local search/dialog, diagram enlargement |
| Publication/QA | Configurable canonical/social URLs, archive/dev indexing policy and sitemap exclusion, clean output, adapter/presentation/link checks, isolated browser/accessibility/performance tooling |

Hugo 0.164.0 and Docsy 0.17.0 remain pinned. Mermaid remains at 11.17.0, rendered on a stable light canvas so appearance changes preserve diagrams and scroll position. No website npm dependency was added. Existing Lunr 2.3.9 is now served locally with its license, instead of depending on its CDN at runtime. QA uses Playwright 1.58.2 and axe-core 4.11.1 separately under `/tmp`.

## Content boundaries

All 180 distinct imported source paths have website-owned navigation classifications. See [documentation-classification.md](documentation-classification.md) for counts and specific upstream proposals. Praxis AI has no guided tutorial in this imported set; its empty tutorial category is omitted. Concise Praxis/AI quickstarts are How-to guides, while the Praxis HTTP filter learning sequence and Policy guided scenario are Tutorials.

Authoritative product prose, generators, build systems, and historical snapshots remain upstream. Preparation changes presentation and links in disposable output only. Unpublished source links resolve to the exact source commit. Product release versions remain independent.

## Validation results

- `make build` passes; the default-domain output was restored after alternate-domain checks.
- `make check` passes, including runnable adapter checks and presentation checks for 670 canonical HTML pages. The same full check passes with `HUGO_BASEURL=https://docs.praxis.example/`; canonical links and 188 sitemap URLs use that domain, with archived/development documents excluded from the sitemap.
- Linkinator scans every generated HTML file, including archives/dev, and checks CSS URLs and fragments: **1,576 links scanned, zero broken internal links**. External destinations are intentionally outside this deterministic check.
- All baseline heading anchors remain present across **660 mapped document routes** after the redesign.
- Homepage and onboarding each expose the three default-release starting guides directly.
- The global search index contains 185 records and is approximately 1.05 MB before compression. It is fetched and indexed on demand; per-product/version scopes and a single scope manifest are generated.
- The minified custom interaction bundle is approximately **3.6 KB gzip**, below the 20 KB budget.

### Browser evidence

Chrome 154.0.8037.92, Playwright 1.58.2, axe-core 4.11.1:

- **130 page/appearance/viewport combinations**: homepage, three product overviews, onboarding, documentation directory, tutorial, how-to, long filter reference, Mermaid explanation, Policy SVG explanation, archive and development pages; widths 320, 390, 768, 1024 and 1440px in both light and dark modes.
- **36 WCAG-tagged axe scans** across representative pages at 390 and 1440px: no reported violations after the highlighting contrast fixes.
- Keyboard search, actual results, Escape/focus restoration, current-product/current-version defaults, shareable form filters, corresponding-page version switching, archive notices, clipboard copy, Mermaid enlargement, theme/scroll preservation, mobile menu/sidebar/TOC all passed.
- The final focused checks also cover mobile source actions, search availability/retry/empty states, additional results, and missing-counterpart version notices.

Evidence: [browser JSON](redesign-evidence/report.json), [final interaction JSON](redesign-evidence/interaction-report.json), [desktop homepage](redesign-evidence/home-light-1440.png), [mobile homepage](redesign-evidence/home-light-390.png). The QA scripts can regenerate the full screenshot set. Automated scans and this interaction review do not establish complete WCAG conformance or exhaustive assistive-technology coverage.

The original link-check skip expression also skipped the local crawler and reported zero links. It now skips external hosts while checking the local server; the all-HTML glob ensures historical versions are included. Actual crawling exposed reference-style and multiline Markdown links the old adapter missed. Those transformations now have runnable checks. The invocation uses file globs and a local server root as described in the [Linkinator CLI documentation](https://github.com/JustinBeckwith/linkinator#command-usage).

### Loading and layout stability

Three uncached local mobile runs at 390×844, 4× CPU slowdown, 150ms latency, and 1.6 Mbps download throughput:

| Serving | LCP runs | CLS | Result |
| --- | --- | --- | --- |
| Uncompressed Python static server | 3.492s / 3.460s / 3.468s | 0 / 0 / 0 | LCP exceeds target |
| Gzip text delivery, verified response headers | 1.200s / 1.140s / 1.144s | 0 / 0 / 0 | Meets LCP ≤2.5s and CLS ≤0.1 targets |

Production hosting must compress HTML/CSS/JS/JSON/SVG responses. The required Docsy stylesheet is about 406 KB before compression; uncompressed transfer dominates the slower result. These are laboratory measurements, not deployed-site field data. Raw evidence: [uncompressed profile](redesign-evidence/performance-uncompressed.json) and [gzip profile](redesign-evidence/performance.json). The QA server and profile are reproducible through [README.md](../README.md).

## Source worktree preservation

All three source worktrees remain clean at their starting revisions:

| Product | Unchanged revision |
| --- | --- |
| Praxis | `3d3bd6fe9c19066ad62bc06eb93157c7010027a2` |
| Praxis AI | `0e9d3d140efab409ffb3583e95f7e58f4a68265a` |
| Policy | `fb94b2b81e5909b72949323921625de7ba7ce328` |

## Remaining source editorial work

The upstream backlog includes quickstart prerequisites/expected outcomes, mixed operator/reference material, and a missing AI tutorial. These are source-maintainer changes, not unfinished website implementation. No publishing, commit, push, or deployment was performed.
