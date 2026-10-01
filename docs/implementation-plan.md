# Praxis website implementation plan

Status: implementation handoff, 2026-09-30. The user approved writing this plan; website implementation will be performed by another model.

## Outcome and decisions

Build one Hugo website using Docsy, with an ecosystem homepage and documentation at `/praxis/`, `/ai/`, and `/policy/`. Product documentation remains authoritative in its source repository. `website/` owns presentation, shared navigation, ecosystem content, and the build that assembles the site.

Use Git submodules at `sources/{praxis,ai,policy}` and Hugo mounts. `.gitmodules` records source repository URLs and paths; the website's tracked Git submodule entries record the exact commits. Adapt existing GitHub-oriented Markdown in disposable build output where necessary. Product prose and generated reference must have one maintained source. The website consumes checked-in reference output; its normal build does not compile the Rust workspaces or run their documentation generators.

Publish independently versioned documentation for each product from the initial implementation. Each product has its own release catalog, default release, and version selector; there is no shared Praxis/AI/Policy version number or combination matrix. Automatic revision updates remain later work.

Read [documentation-architecture-research.md](documentation-architecture-research.md) for the researched alternatives and primary sources. Recheck the official Hugo and Docsy requirements when selecting their pinned versions.

## Repository boundary: website owns the integration

The initial implementation must consume the existing `praxis/`, `ai/`, and `policy/` repositories without requiring changes to their files, build systems, dependency manifests, documentation generators, or CI workflows. Treat their documentation, diagrams, examples, and checked-in generated reference as read-only inputs. The existing sibling checkouts must remain untouched.

Keep the website dependencies and integration changes in `website/`:

| Concern | Location and rule |
| --- | --- |
| Hugo, Docsy, Sass/JavaScript dependencies, link checker, adapter tooling | Website configuration, manifests/lockfiles, Makefile, and CI; use only tools needed by the selected theme/build |
| Source selection and historical-layout differences | Website import configuration and narrow path overrides |
| Front matter, titles, navigation weights, Diátaxis grouping, index adaptation | Website metadata/configuration and disposable prepared content |
| Markdown/image link resolution and version-scoped resources | Website adapter, Hugo mounts, and render hooks where necessary |
| Version catalogs, selectors, banners, search, and latest aliases | Website data, templates, and configuration |
| Downloaded tool caches, extracted snapshots, generated pages, and check results | Ignored website directories or temporary build directories |
| Build, checks, release selection, and publication | Website Makefile and workflows |

In particular, adding Hugo metadata or renaming source `README.md`/`index.md` files must not be prerequisites. Adapt those forms in prepared output. Do not add Hugo modules, package manifests, website scripts, dependencies, or release-trigger workflows to the three source repositories. Do not run their Makefiles or generators during website preparation to make them website-compatible. If an upstream-generated reference needs regeneration, report it as a separate source-maintainer task and consume an already-published corrected revision when available.

Use standard native dependency files where tools require them, with all pins and install/check commands owned by the website. Theme or tooling commands that mutate their working directory must run from the website or disposable staging directories. Containerized preparation, if used, mounts source content read-only and places output in a separate website directory. Installing the website must not require installing the Rust workspaces' compiler toolchains or test infrastructure.

Cloning/fetching submodule Git objects and explicitly updating a website-recorded submodule pointer are part of website dependency management; changing source tracked files is a separate concern. Preserve populated source checkouts as described in step 2.

If existing content exposes an error that cannot be handled by a bounded website adaptation, record the exact upstream issue and a proposed follow-up. Keep factual corrections in the authoritative source rather than introducing an editable product-prose fork. Any source-repository fix is outside this website implementation and requires separate user authorization. Report the affected page and any remaining publication limitation explicitly.

## Ownership and initial sources

| Owner | Authoritative content | Website responsibility |
| --- | --- | --- |
| `praxis-proxy/praxis` | Proxy guides, architecture, configuration, filter reference, examples | Publish under `/praxis/` |
| `praxis-proxy/ai` | AI gateway guides, provider integrations, AI filter reference, examples | Publish under `/ai/` |
| `praxis-proxy/policy` | PPE guides, APL, identity, delegation, threat model, diagrams | Publish under `/policy/` |
| Website repository | Ecosystem introduction, cross-product guides, community, site contribution instructions | Shared content and presentation |

Initial public-content candidates:

- Praxis: `docs/quickstart.md`, `docs/features.md`, `docs/architecture/`, `docs/operating/`, `docs/filters/`, selected development and release guides.
- AI: `docs/quickstart.md`, `docs/features.md`, `docs/architecture/`, `docs/filters/`, provider guides, selected development, release, and conformance guides.
- Policy: `docs/content/`, with referenced diagrams from `docs/images/`.

Inventory the actual files before choosing import rules. Keep public guides distinct from plans, brainstorms, replay investigations, raw conformance specifications, fixtures, and generator inputs. Prefer a small explicit set of public files/directories over importing entire repositories. The planning notes in website `docs/` are outside the published content tree.

Local checkouts inspected during planning:

| Repository | Inspected commit |
| --- | --- |
| Praxis | `1de023cba3fee967f828c9ff35f27596f8f6792c` |
| AI | `0e9d3d140efab409ffb3583e95f7e58f4a68265a` |
| Policy | `fb94b2b81e5909b72949323921625de7ba7ce328` |

These are orientation anchors, not a requirement to publish those exact commits. Select remotely available revisions deliberately and record them. Local changes are not part of a pinned production build.

## Implementation sequence

### 1. Establish the website build

Inspect repository instructions and existing files before editing. At planning time, `website/` has no site scaffold or commits; it contains only the research note and this plan.

- Select compatible Hugo and Docsy versions from their current official requirements; pin the theme and build tools.
- Put dependency manifests, lockfiles, bootstrap instructions, and any required package scripts in website. The Makefile checks prerequisites and resolves website dependencies without altering source repository manifests or installing unrelated product toolchains.
- Use Docsy as a Hugo module and retain its standard layouts, accessibility behavior, and responsive navigation.
- Add the smallest site configuration, homepage, three product section landing pages, and community page.
- Configure product documentation sections with Docsy's `docs` content type. The ecosystem homepage retains its landing-page layout.
- Provide the Makefile interface specified in step 2. Use the same preparation/build path in local development and CI.
- Track `.gitmodules` and the three submodule entries. Ignore prepared content, generated resources, and `public/` output; `sources/` must remain visible to Git as tracked submodules.

Completion: the scaffold builds locally; the homepage and all three product landing pages render with consistent navigation at the proposed paths. No placeholder product claims are published.

### 2. Add submodules and the Makefile interface

Add the three source repositories as submodules with HTTPS URLs under `sources/`. Select published commits, then record each submodule pointer in the website repository. Git is the source of truth for acquisition and the working-source revision; no `docs-sources.json` is required. A separate version catalog is needed to select historical snapshots from each repository, as specified in step 6. Keep tool versions in their native configuration files. Content selection and metadata overrides belong in Hugo configuration or a small adapter configuration only where needed; they do not repeat repository URLs or the working-source commit pins.

Provide this contributor interface:

| Command | Behavior |
| --- | --- |
| `make help` | Describe the targets and required build tools |
| `make init` | Initialize missing source submodules at the committed pointers, acquire missing cataloged release objects, and resolve the pinned theme dependencies |
| `make build` | Initialize missing dependencies, verify clean source checkouts at committed pointers, prepare every cataloged snapshot, and build the complete Hugo site |
| `make serve` | Initialize missing dependencies, prepare docs, and start local preview; allow source edits and explicitly report preview revisions/dirty state |
| `make check` | Build through the same path and run the generated-site internal-link/resource checks |
| `make update-docs PRODUCT=policy REF=<tag-or-commit>` | Fetch the selected source and move that submodule to the requested commit for review |
| `make add-docs-version PRODUCT=policy REF=<release-tag>` | Resolve a release tag to a full commit SHA and add a reviewable version-catalog entry; leave default-release promotion explicit |
| `make clean` | Remove disposable website build output while retaining source submodules and authored files |

Initialization must preserve populated submodules, including local edits and deliberately selected preview commits. Initialize only missing checkouts; build verification reports mismatched or dirty sources with actionable instructions rather than silently resetting them. Ordinary builds do not advance sources to remote branch heads. Fetch missing cataloged objects without changing the working checkouts; once required objects exist, source preparation needs no network fetch until an explicit update introduces another revision. A shallow CI checkout must acquire enough history to resolve every catalog entry.

`make update-docs` validates the product name and requires an explicit ref. It refuses to replace a dirty selected checkout, resolves the requested ref to a fetched commit, and checks out that commit without staging, committing, or pushing the website pointer. Document that the contributor reviews the diff, stages `sources/<product>`, and commits the pointer in a website PR. Restoring a recorded revision must likewise be explicit and preserve local work. Show `git diff --submodule=log` as the review command.

For a future separately authorized source-documentation contribution, edits are committed and published in the originating repository before updating the website pointer. Explain detached submodule checkouts and how to use a source branch for contribution; source contributions are not prerequisites for implementing the website. Existing sibling repositories remain useful for development; the required preview path is the submodule checkout, so a separate sibling override mechanism is unnecessary initially.

Product versions remain independent. The submodule pointer supplies each optional development snapshot; cataloged releases use their own immutable commits. Show the version and actual commit for each published snapshot. Updating a working-source pointer updates its development docs, while adding or promoting a release is an explicit catalog change.

Completion: `make build` works from a fresh non-recursive website clone by initializing the sources. Rebuilding identical source and tool revisions produces equivalent published content. `make serve` preserves local documentation edits; `make build` reports dirty/mismatched sources; updating one submodule produces a reviewable pointer change without changing the other two.

### 3. Import and adapt the existing Markdown

Use Hugo mounts for the content and resources. Retain the website's own `content` mount explicitly when adding imported content mounts.

The current docs are plain Markdown, including generated files without Hugo front matter. Use a small deterministic preparation step to create ignored content under `.cache/docs/{product}/{version}` when metadata or index adaptation is needed. Hugo mounts that prepared content under the corresponding product/version section. This is disposable build output, never an editable documentation fork. Apply the same adapter to every selected release, allowing narrow path overrides where older repository layouts differ.

The preparation step has a bounded job:

- Select the public documents and preserve their relative hierarchy initially.
- Supply titles and required Docsy metadata. Derive ordinary page titles from the first heading; use explicit overrides for exceptions and section ordering.
- Map directory landing documents to `_index.md` when their children must remain pages. Inspect `README.md` and `index.md` individually: a Hugo leaf `index.md` can otherwise hide documentation beneath it.
- Preserve Markdown bodies, code fences, generated-file notices, and existing heading anchors. If removing a repeated page heading, retain its anchor for incoming links.
- Preserve a mapping from each published page to its product, version, original repository path, and snapshot revision, including renamed indexes.
- Publish referenced images in product/version-scoped locations so old diagrams remain coupled to old docs. Account for policy's images outside `docs/content/` and AI assets outside `docs/`.

Keep this an adapter for the observed source layouts. Reuse native Hugo behavior wherever it handles a case. Avoid building a general Markdown conversion framework. Keep adaptation metadata and any focused adapter-check fixtures in website; existing source files and generator outputs retain their original format.

Completion: every selected source document has one intended published page; nested policy APL pages render; generated filter reference and diagrams display; prepared files can be deleted and recreated without losing authored content.

### 4. Resolve links and contribution targets

Choose the resolver supported by the pinned Hugo/Docsy versions before writing custom render hooks. Native embedded hooks can resolve Markdown page links, but unresolved destinations do not automatically fail the build.

Handle these cases explicitly:

| Link kind | Required result |
| --- | --- |
| Relative documentation `.md` link | Correct generated page within the same product/version, preserving query/fragment where applicable |
| `README.md` or `index.md` link | Correct mapped landing page |
| Relative diagram/image | Published resource under the correct product/version prefix |
| Example config or source file outside imported docs | Repository blob at the recorded revision, or a deliberately published download |
| Documentation in another Praxis repository | Explicit target release when the source identifies one; otherwise that product's default docs, without assuming matching version numbers |
| External link | Preserve its external destination |

Use the original source-path mapping to resolve renamed documents and repository-relative links. Distinguish deliberate source-code links from documentation links; avoid rewriting every GitHub URL indiscriminately.

Configure Docsy repository-link metadata per product/version. View-source links must identify the snapshot's exact commit. Development edit links target the originating contributor branch and exact original path. For release snapshots, expose an edit target only when a maintained documentation branch is explicitly configured; otherwise provide view-source and issue links plus instructions for contributing a correction. Avoid presenting an edit link to a release tag or an unrelated current file as an edit to the archived snapshot. Website-owned pages target the website repository. Use supported Docsy path mapping; add a narrow override only if staged index renames cannot be represented correctly.

Completion: navigation, Markdown links, diagrams, and edit links work for representative pages in every product. A generated-site internal-link check also passes for all imported pages, including fragments. Do not rely on Hugo build success alone.

### 5. Apply Diátaxis to the first reader journeys

Keep page purpose explicit:

| Reader need | Content form | Initial Praxis journey |
| --- | --- | --- |
| Learn by doing | Tutorial | Run a proxy, send a request, observe a filter result |
| Complete a task | How-to guide | Route an AI model or configure permission-based redaction |
| Look up behavior | Reference | Filter fields, configuration options, APL grammar |
| Understand reasons | Explanation | Pipeline composition, reference monitor, session taint |

Classify existing pages by their contents rather than filenames, using website-owned metadata and navigation. Improve website landing pages and links before adding category landing pages; create navigation groups when useful imported content supports them. Diátaxis adoption in this implementation changes the website presentation, not the source prose or directory structure. Record recommended product-documentation rewrites as separate follow-ups. Retain existing stable product paths where practical and add aliases when moving a published page.

Make the product landing pages direct readers to getting started, practical tasks, reference, and conceptual material. Cross-product guides belong in website content and link to the authoritative product pages.

Copy must preserve the project distinctions: Praxis is the proxy framework, Praxis AI is its AI gateway, and PPE is a policy runtime. Describe alpha status, feature gates, scoped compatibility, and FIPS host requirements accurately. Recheck versions and integration dependencies at the selected revisions: the inspected Praxis manifest depends on PPE `0.3.1`, while the inspected Policy checkout is `0.4.0`.

Completion: a new reader can select a starting path for each product; existing users can find reference directly; product claims are traceable to the imported documentation. Imported product prose remains unchanged, with editorial corrections documented for separate source-maintainer follow-up.

### 6. Publish independent product versions

Reference pattern: Coraza Kubernetes Operator's `docs/versions.yaml` enumerates named versions, source refs, display labels, and one default. Its `hack/build-versioned-docs.sh` extracts tagged sources with `git archive`, generates version metadata, publishes version subpaths, and consolidates the output into one Pages artifact. Its version banner distinguishes development and archived content. This was inspected in the local checkout at `/home/rpchevuz/codes/work/waf/coraza-kubernetes-operator`, commit `bcd03f395d429234024b7a0246fad569d3fdbde5`; the upstream repository is linked in the references.

Adapt the catalog and snapshot pattern while retaining one aggregate Hugo site and one publication. Coraza's site-wide selector serves one product. Praxis needs a selector scoped to the current product; Docsy's global `params.versions` alone does not express three independent catalogs.

**Version catalog.** Add one small website-owned data file, such as `data/docs_versions.json`, grouped by `praxis`, `ai`, and `policy`. Each release entry has a full release-version slug, display label, informational tag, full resolved commit SHA, and a default marker. Every product must have exactly one default published release. An optional `dev` entry reads its commit from the recorded submodule pointer, so that working-source pin is not duplicated. The catalog is publication metadata for historical revisions, not a replacement for `.gitmodules` or an automatically discovered list of remote tags.

- Use full release versions for immutable paths, such as `v0.7.2`, rather than silently changing a minor-version snapshot when a patch ships. Validate slugs, duplicate entries, commit availability, and tag/commit agreement when acquiring a release.
- Choose each product's initial released versions independently: its current published release and at least one previous release with usable docs where available. Include `dev` for each product using its pinned submodule source. Record any unavailable historical documentation explicitly instead of fabricating a release or silently omitting a cataloged snapshot.
- Default means latest selected release, including an alpha release where applicable. It does not assert production stability or security support.

**URL contract.** Product landing pages remain `/praxis/`, `/ai/`, and `/policy/` and link directly to their own default release. For illustration only:

```text
/praxis/v0.7.2/...      /praxis/dev/...
/ai/v0.4.1/...          /ai/dev/...
/policy/v0.4.0/...      /policy/v0.3.1/...      /policy/dev/...
```

Confirm tags and docs exist before selecting the actual initial versions. Add `/PRODUCT/latest/` aliases for the default release landing page and its documents using Hugo aliases. Release URLs stay stable; only `latest` aliases change on default promotion. Aliases point to canonical release URLs rather than creating separately indexed duplicate content.

**Snapshot build.** Extract the necessary documentation/resources from cataloged commits with `git archive` or an equivalent read-only Git operation into ignored temporary directories. Build all snapshots with the website's pinned Hugo/Docsy theme and the existing adapter. Keep original source checkouts, branches, and submodule pointers intact. Extract example/source-file links from the snapshot context, including its correct commit. Production `dev` uses the recorded Git commit; local preview may use working-tree content and identifies that difference visibly. Preparation must fail if a selected release's required documentation cannot be imported.

**Navigation and banners.** Attach product and version metadata to each imported page. Use the standard Docsy selector component if its pinned implementation can accept a scoped catalog; otherwise add a narrow selector partial override using the current product's data. Do not copy the whole navbar merely to supply a different version list. The selector must be keyboard accessible and visible on mobile.

- A Policy page lists only Policy versions; switching does not change Praxis or AI defaults. Shared ecosystem pages have no artificial ecosystem version selector.
- Initially, switching versions goes to the target version's landing page. Do not enable automatic same-page switching without checking target-page existence; Docsy warns that blind page switching can produce broken links.
- Display the active version. Non-default releases show an archived-docs notice with a link to that product's default. Development pages show an unreleased-content notice. Documentation archival and software security-support status are separate facts.
- Sidebar links, breadcrumbs, diagrams, reference links, and ordinary intra-product links stay within the active version. Cross-product links follow the explicit rules in step 4.
- Search identifies product/version for every result. The default search experience covers all products' default releases; archived and development results require explicit version selection or filtering. Use a supported search configuration where possible, with a small scoped adaptation only if needed.

**Release updates.** `make add-docs-version` adds a resolved historical snapshot without moving source checkouts or promoting defaults. The maintainer reviews its content and selects the default in the catalog. Rebuild all published versions and verify selector entries, latest aliases, and version labels before publishing. Retain previous release URLs when promoting a new default. Removing an archive requires a deliberate catalog change and a documented redirect/retention decision. Source-pointer and catalog changes remain website PRs.

Completion: each product has an independent catalog and working selector; configured release snapshots coexist in one generated site. Promoting Policy's default changes only Policy's default links, aliases, and banner state. A prior release page and its diagrams remain available at the same version URL; the versioned build leaves submodules unchanged.

### 7. Add CI and prepare publishing

- GitHub Actions checks out the website with `submodules: true`, acquires the cataloged historical commits, then invokes `make check` for pull requests. Initialize only the three direct source submodules unless an imported resource actually requires nested submodules. Check every published snapshot and latest alias. Use an existing maintained link checker rather than implementing a crawler.
- Pin CI actions to immutable revisions and grant deployment permissions only to the deployment job. Pull-request validation requires no publishing credentials.
- Publish one complete Pages artifact from the protected default branch through GitHub's Pages actions. Serialize deployments so an older build cannot replace a newer publication.
- Keep source updates manual through `make update-docs` and release additions through `make add-docs-version` for the initial implementation. A later automation may open update PRs using the project's existing GitHub App pattern. Production CI consumes committed pointers and cataloged immutable SHAs; it never selects remote branch heads or discovers new releases implicitly.
- Keep all CI changes in website. Source repositories need no new workflow, webhook, secret, or release job to support publication. Any later update automation should remain website-owned unless the user explicitly chooses a source-side integration.
- Document how to preview a product documentation change before updating the production pin and how to revert an update by reverting its website pointer/catalog change.

Hosting decision: the local folder remains `website/`. For the exact root `https://praxis-proxy.github.io/`, prefer the remote repository name `praxis-proxy.github.io`. A remote named `website` normally receives `/website/`; if that name is retained, use a separate organization Pages publishing repository or an explicitly selected custom domain. Confirm the actual remote and Pages settings before enabling production publication. Configure `baseURL` for that destination and verify asset paths under it.

Completion: CI builds a deployable artifact, checks fail on a broken internal link, and publishing setup is documented for the chosen remote. Creating files and a workflow does not authorize the implementing model to rename repositories, configure external services, push, or deploy; perform those actions only when the user authorizes them.

## Acceptance and handoff

The implementation is ready for review when:

- `make build` initializes a fresh clone and builds using recorded submodule pointers; `make check` uses that build path in CI.
- Initialization and preview preserve populated submodules and local documentation edits; production builds reject dirty or mismatched source checkouts with a clear diagnostic.
- `make update-docs` changes only the requested submodule, requires a ref, and leaves its pointer change available for review; `make clean` retains source checkouts.
- `make add-docs-version` resolves and records a release without changing source checkouts; builds fetch missing historical objects and import every configured snapshot.
- `/`, `/praxis/`, `/ai/`, `/policy/`, and `/community/` render with consistent responsive navigation.
- Every product exposes independent release/dev paths, a scoped version selector, and correct default-release aliases. Archives retain their own prose, diagrams, and commit-specific source links.
- Promoting one product's default preserves older version URLs and leaves the other products' defaults unchanged. Selectors and banners work on mobile and with keyboard navigation.
- Search covers all products' default releases and identifies/filter-scopes historical and development results by product/version.
- All selected pages, diagrams, internal links, and fragments pass generated-output checks.
- Product edit links reach the original files, including adapted indexes; source links identify the documented revisions.
- Importing the docs leaves source repositories unchanged and creates no tracked copies of product prose in website content.
- All website dependency manifests, lockfiles, Makefile targets, adaptation configuration, templates, checks, and CI changes are inside website. The implementation requires no source-file, source-generator, source-build, or source-CI changes.
- Initialization/build/check runs leave source tracked files and existing sibling checkouts unchanged; snapshot/adaptation output stays in ignored website or temporary directories. Report source worktree status before and after the implementation, preserving any pre-existing changes.
- Source/version labels and ecosystem claims accurately describe the selected revisions.
- The implementation report lists changed files, executed checks, source revisions, source-worktree preservation, and any external hosting step still awaiting authorization. Necessary upstream documentation corrections are listed separately from completed website work.

Leave automatic cross-repository dispatch, translations, and a broad Diátaxis rewrite for later requirements. Independent versioned documentation is part of the initial scope.

## Primary references

- [Hugo mounts](https://gohugo.io/configuration/module/) and [module usage](https://gohugo.io/hugo-modules/use-modules/): assemble external content without independent sites.
- [Hugo page bundles](https://gohugo.io/content-management/page-bundles/) and [link render hooks](https://gohugo.io/render-hooks/links/): index semantics and Markdown link resolution.
- [Docsy content](https://www.docsy.dev/docs/content/adding-content/), [navigation](https://www.docsy.dev/docs/content/navigation/), and [repository links](https://www.docsy.dev/docs/content/repository-links/): custom documentation sections and originating-repository metadata.
- [Docsy versioning](https://www.docsy.dev/docs/content/versioning/): version selectors, archive banners, and limitations of automatic page switching.
- [Coraza Kubernetes Operator](https://github.com/networking-incubator/coraza-kubernetes-operator/), especially `docs/versions.yaml`, `hack/build-versioned-docs.sh`, and `docs/layouts/partials/version-banner.html`: inspected reference for cataloged snapshots and consolidated publication.
- [Git submodules](https://git-scm.com/docs/gitsubmodules) and [GitHub checkout](https://github.com/actions/checkout): repository paths, committed source revisions, and CI initialization.
- [Pages site types](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) and [custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages): publication.
- [Diátaxis primer](https://diataxis.fr/start-here/) and [application guidance](https://diataxis.fr/how-to-use-diataxis/): reader needs and incremental documentation improvement.
