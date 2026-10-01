# Documentation publishing architecture

Research date: 2026-09-30. This is a planning note; no site configuration or deployment was created.

## Recommendation

Keep product documentation authoritative in `praxis/`, `ai/`, and `policy/`. Let `website/` own the Hugo and Docsy configuration, presentation, navigation, ecosystem overview, and material that spans products. Publish one generated site with product sections at `/praxis/`, `/ai/`, and `/policy/`.

Following the user's planning decision, use Git submodules under `website/sources/`, followed by Hugo mounts. Git's submodule entries pin source commits, and `.gitmodules` records repository URLs and paths. This preserves documentation updates alongside code changes while giving readers one website and a consistent information architecture. The [implementation plan](implementation-plan.md) specifies Makefile targets to handle initialization, preview, checks, and explicit pointer updates. [Git submodule documentation](https://git-scm.com/docs/gitsubmodules)

Repository boundary agreed with the user: the website implementation treats all three product repositories as read-only content sources. Dependencies, import metadata, Markdown/index adaptation, link handling, version presentation, checks, and publishing workflows live in website. Existing source docs require no Hugo front matter, renames, new manifests, or generator changes. Adapt content in ignored staging output and record genuine upstream documentation corrections as separate follow-ups; the plan contains the implementation requirements and acceptance criteria.

## Supported mechanisms

| Approach | Assessment for Praxis |
| --- | --- |
| Move all docs into `website/` | Simple website build, but code and documentation changes require separate repository changes. Appropriate for shared ecosystem pages, less suitable for product configuration and generated reference. |
| Git submodules and Hugo mounts | Selected approach. Git tracks source URLs, paths, and commit pointers. Makefile targets handle initialization and explicit updates. Hugo consumes the source documentation without a tracked duplicate of its prose. |
| Separate checkouts and a revision manifest | Valid alternative, but requires maintaining acquisition and pinning that Git submodules already provide for these three fixed sources. |
| Import source repos through Hugo modules | A valid alternative. Hugo modules provide dependency versions, checksums, caching, and mount configuration. More useful if documentation becomes a reusable package consumed by several websites; unnecessary to require each Rust repository to maintain a complete Hugo site. |
| Build separate sites for each product | GitHub Pages supports project sites at repository subpaths. This permits independent deployments, but theme, navigation, search scope, and cross-product links require coordination. Use if product teams need independent site behavior or release publishing. |

Supporting sources: [GitHub checkout action](https://github.com/actions/checkout#checkout-multiple-repos-side-by-side), [Hugo module usage](https://gohugo.io/hugo-modules/use-modules/), [Hugo mount configuration](https://gohugo.io/configuration/module/), [GitHub Pages site types](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

Checkouts and mounts perform different jobs: Git obtains a particular revision; a mount maps its documentation into Hugo's content tree. The same mounts can later be supplied by remote Hugo module imports. When adding custom content mounts, explicitly retain the local `content` mount because defining mounts for a component replaces its default mount. [Hugo mount configuration](https://gohugo.io/configuration/module/)

## Existing content needs an adaptation pass

Local inspection found these candidate public documentation roots:

- `praxis/docs/`: architecture, filters, operations, development, quickstart, and generated reference.
- `ai/docs/`: features, filters, quickstarts, provider integration, and conformance material.
- `policy/docs/content/`: product documentation; diagrams live separately in `policy/docs/images/`.

These are not ready-made Hugo content trees. For example, `policy/docs/content/index.md` has no front matter; its overview refers to `../images/overview_outcomes.svg`. Praxis's quickstart links to `filters/README.md`, and AI's features page links outside `docs/` to `../examples/README.md`. Policy's `docs/` also contains plans, brainstorms, and development material that should not all be published automatically.

Choose public pages explicitly, supply titles/navigation weights through website metadata, and create adapted section `_index.md` files in disposable prepared content. Source `README.md`/`index.md` names remain unchanged. Hugo treats `index.md` as a leaf bundle and `_index.md` as a section index; existing GitHub-oriented indexes therefore need review. Docsy supports a custom top-level section using its `docs` content type, allowing `/policy/` without another site build. This differs from Docsy's experimental documentation-at-site-root mode. [Docsy content structure](https://www.docsy.dev/docs/content/adding-content/), [Hugo page bundles](https://gohugo.io/content-management/page-bundles/)

Preserve Markdown links that remain readable in GitHub where possible. Hugo's embedded link render hook can resolve Markdown destinations to pages and resources, but unresolved destinations do not automatically fail a build. Check the chosen Docsy version's hooks before selecting a resolver; mount images into suitable resource or static locations and check output links. Mounting files alone does not translate every existing repository path into a working public URL. [Hugo link render hooks](https://gohugo.io/render-hooks/links/)

Docsy builds its sidebar from the content hierarchy and page metadata. Its repository link settings support section-specific originating repositories through `github_repo`, `github_subdir`, and `path_base_for_github_subdir`, including path renames. Set these so edits return to the appropriate source repo. [Docsy navigation](https://www.docsy.dev/docs/content/navigation/), [Docsy repository links](https://www.docsy.dev/docs/content/repository-links/)

## Publishing and revisions

For exactly `https://praxis-proxy.github.io/`, GitHub requires the organization Pages repository to be named `praxis-proxy.github.io`. A repository named `website` normally publishes at `/website/`. Local directory naming can remain `website/`; alternatively, retain a separate `website` repository and have a workflow in the organization Pages repository check it out and deploy its generated artifact. The latter is an architectural inference from the official checkout and custom Pages workflow support. [Pages site types](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

Record the three working-source revisions as tracked submodule pointers; keep Hugo and Docsy pins in their native configuration. Independent historical documentation is now required in the initial scope: maintain a publication catalog per product with immutable release SHAs, one default release, and an optional development entry derived from the submodule pointer. Begin with manual pointer and catalog updates through website pull requests. This makes a published build reproducible and lets its documentation combination be reviewed. An update to a source repository does not inherently update the website's pinned revision. GitHub Actions supports submodule initialization through the checkout action's `submodules` option. [Git submodule documentation](https://git-scm.com/docs/gitsubmodules), [GitHub checkout](https://github.com/actions/checkout)

Later, if publication latency becomes a problem, prefer website-owned automation that opens pointer/catalog update PRs. Source-side dispatch is an optional separately authorized integration rather than a website prerequisite; a pinned build still needs its committed pointer/catalog changed. Cross-repository private access needs credentials scoped to the destination repository; the default checkout token is scoped to its current repository. Existing project guidance already uses a GitHub App for bot actions. Scheduled checks have GitHub-documented delays and inactivity limitations. [Workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#repository_dispatch), [checkout authentication](https://github.com/actions/checkout#checkout-multiple-repos-private)

Document release compatibility explicitly. Local context identifies Praxis's PPE dependency as `0.3.1` while the sibling Policy checkout is `0.4.0`; publishing the three newest branches must not imply those versions are all integrated. Publish release snapshots at independent `/PRODUCT/vX.Y.Z/` paths, with product-scoped selectors and `/PRODUCT/latest/` aliases. Promoting one product leaves the others' defaults unchanged.

Versioning reference: the local Coraza Kubernetes Operator checkout at `/home/rpchevuz/codes/work/waf/coraza-kubernetes-operator`, commit `bcd03f395d429234024b7a0246fad569d3fdbde5`, contains a `docs/versions.yaml` catalog, `git archive` extraction in `hack/build-versioned-docs.sh`, version subpath builds consolidated into one artifact, and a development/archive banner. Its catalog lists `latest`, `v0.4`, and `dev`. This observation is from the local source checkout; upstream web retrieval was unavailable during this update. Adapt the snapshot/catalog pattern, with three independent product catalogs and selectors in the aggregate Praxis site. [Upstream repository](https://github.com/networking-incubator/coraza-kubernetes-operator/)

Docsy provides site-wide version selectors and archive banners but leaves snapshot deployment to the project. Its automatic same-page selector can create broken links when pages are absent in another version. Scope a reused selector or narrow partial override to product metadata, and initially switch to each version's landing page. [Docsy versioning](https://www.docsy.dev/docs/content/versioning/)

Use Diátaxis within each product's documentation: tutorials, how-to guides, reference, and explanation. Keep cross-product material in `website/` and classify existing pages by the reader need they actually serve. The publishing mechanism and the editorial classification are separate decisions.
