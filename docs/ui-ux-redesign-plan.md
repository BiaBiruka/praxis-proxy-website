# Praxis website redesign with Hugo, Docsy, and Diátaxis

Status: implemented and validated, including the skill-guided revision on 2026-09-30. The user approved retaining Hugo and Docsy and requested this document as a future reference. Following feedback about colors, typography, broken layout, and developer-heavy onboarding, the revision applies the recommended UI skills and updates the visual tokens and audience priorities below. See [skill-guided-revision.md](skill-guided-revision.md) for the current changes and evidence, and [redesign-implementation-report.md](redesign-implementation-report.md) for the first pass.

This plan builds on [implementation-plan.md](implementation-plan.md) and [documentation-architecture-research.md](documentation-architecture-research.md). Their source ownership, reproducible build, independent versioning, and repository boundary requirements remain in effect.

## 1. Goals and required architecture

Create an appealing ecosystem website that helps new technical users understand the products, choose a starting point, and find dependable documentation.

**Hugo and Docsy remain the required foundation.** Retain the existing Hugo module integration, pinned theme, Docker build/serve commands, Git submodules, Hugo mounts, and independently versioned product documentation.

Use Docsy's layouts, responsive navigation, appearance modes, highlighting, copy controls, and Mermaid support. Customize through project SCSS, Hugo data, shortcodes, and narrow partial overrides. See [Docsy content structure](https://www.docsy.dev/docs/content/adding-content/) and [Docsy navigation](https://www.docsy.dev/docs/content/navigation/). Check features against the locally pinned theme version before using examples from newer online documentation.

The website owns presentation, navigation metadata, ecosystem introductions, and shared onboarding. Product repositories remain authoritative for product prose, examples, and reference. Adapt their content in disposable build output; preserve existing document URLs, source mappings, and historical snapshots.

### Research and browser audit

The audit covered desktop and mobile homepages, a product landing page, a quickstart, and an architecture page. It identified these priorities:

| Finding | Planned improvement |
| --- | --- |
| Homepage consists of a paragraph and three large stacked links | Introduce a clear promise, ecosystem explanation, and guided starting points |
| Default Docsy logo, typography, colors, and largely empty footer | Establish a recognizable identity and consistent visual hierarchy |
| Product pages expose repetitive documentation-version listings | Give each product a purposeful overview with a prominent starting action |
| Quickstarts and architecture pages repeat their main heading | Normalize headings during website preparation while preserving anchors |
| Sidebar mixes beginner tasks, reference entries, and development internals | Organize navigation around reader needs and the selected version |
| Search descriptions are generic; the inspected global index approaches 1 MB and loads immediately | Provide meaningful results, explicit scopes, and loading on demand |
| Mobile homepage has no visible search control | Make search available throughout the site at every viewport |
| Source/edit/create-page actions compete with the article and table of contents | Consolidate contribution actions into a small, accurate metadata area |
| Existing diagrams are buried within documentation | Surface ecosystem relationships and improve diagram presentation |

Four Mermaid diagrams rendered on the inspected Praxis architecture page. Policy also includes explanatory SVGs. Reuse and improve the presentation of these existing assets.

The information-design recommendation draws on Cloudflare's distinction between an orienting overview and a bare table of contents, and Astro's separation of beginner guidance from reference. These are design references, not templates to copy. See [Cloudflare overview guidance](https://developers.cloudflare.com/style-guide/documentation-content-strategy/content-types/overview/) and [Astro documentation](https://docs.astro.build/en/getting-started/).

### Agreed direction

- Primary audience: **product users and operators configuring existing behavior**. Put practical configuration guides first; provide custom Rust extension instructions as a distinct developer path.
- Visual direction: **technical editorial design**, with distinctive typography, neutral surfaces, restrained product accents, and explanatory graphics.
- Scope: **the whole website in phases**, including homepage, product overviews, navigation, reading, search, diagrams, and accessibility.
- Identity: **a simple custom vector identity** and a coherent product-symbol family.
- Appearance: **light, dark, and system modes**, following the operating system by default.
- Primary onboarding: **choose by task**, rather than making one product the mandatory entry.

## 2. Apply Diátaxis to content, navigation, and discovery

Diátaxis will guide classification and editorial improvements, rather than serve only as a set of navigation labels. It distinguishes learning, accomplishing a task, looking up facts, and understanding concepts. See the [Diátaxis framework](https://diataxis.fr/).

| Documentation form | Reader need | Presentation and editorial requirements |
| --- | --- | --- |
| **Tutorials** | “Help me learn by doing.” | Guided sequence, explicit prerequisites, a bounded learning outcome, expected results, and a next step |
| **How-to guides** | “Help me accomplish this task.” | Task-focused title, necessary assumptions, actionable steps, and links to supporting reference |
| **Reference** | “Tell me the precise details.” | Consistent terminology, predictable structure, accurate tables and code, and easy lookup |
| **Explanation** | “Help me understand why and how.” | Concepts, relationships, architecture diagrams, context, and tradeoffs |

### Classification

Extend the existing `reader_need` metadata beyond the handful of configured reader journeys. Classify public articles by their actual purpose, with website-owned source-path overrides where needed.

Initial examples:

- Praxis HTTP filter tutorial: **Tutorial**.
- Policy's guided first-policy scenario: **Tutorial**.
- Concise build/run/configuration recipes: **How-to guides**, unless their content genuinely teaches through a guided learning experience.
- Generated filter documentation and APL grammar: **Reference**.
- Architecture, threat models, and design rationale: **Explanation**.

A filename such as `quickstart.md` or its directory does not determine its classification. Mixed documents receive a primary classification and an upstream improvement note describing any recommended split or rewrite.

Overview, navigation, release, and ecosystem pages retain their appropriate roles; they do not need to be forced into one of the four article forms.

### Navigation

Each product documentation overview presents the supported reader needs:

- **Tutorials:** learn through a guided example.
- **How-to guides:** configure, integrate, deploy, and operate.
- **Reference:** inspect configuration, filters, protocols, and language details.
- **Explanation:** understand architecture, security, and design choices.

Pin a prominent **Get started** route above these groups. Within them, retain useful topic subdivisions such as operations, integrations, filters, and APL.

Render groups only where useful content exists. Record missing tutorials or other content as an editorial backlog instead of publishing empty category pages. This follows Diátaxis's guidance to improve existing material incrementally. See [Applying Diátaxis](https://diataxis.fr/how-to-use-diataxis/).

Keep original article URLs. Group Hugo page collections using prepared metadata, with a narrow Docsy sidebar override where needed. Scope navigation to the current product and version; use Docsy's native collapse and active-page behavior.

Store presentation overrides in `data/docs_navigation.json`, referencing original source paths. Include primary reader need, topic, ordering, summary overrides, and selected related pages. Resolve links through the existing source mapping and keep reader-journey labels consistent with this classification.

### Editorial boundaries

Improve website-owned onboarding immediately. For authoritative product documentation, record specific upstream proposals—for example, missing prerequisites, absent expected results, or reference material embedded in a tutorial.

Preserve archived prose. Apply presentation and classification improvements without turning historical documentation into rewritten current documentation.

Product source files, their generators, and their build systems remain read-only inputs to this redesign. An upstream correction is a separate source-maintainer task; do not create an editable product-prose fork in the website.

## 3. Identity, homepage, and visitor experience

### Visual foundations

Use Docsy's supported project styling hooks and native appearance controls. See [Docsy customization](https://www.docsy.dev/docs/content/lookandfeel/).

- **Identity:** a Praxis wordmark and an SVG symbol based on converging routing paths. Related product symbols represent routing, inference, and policy boundaries.
- **Typography:** self-host IBM Plex Sans for interface/article text and IBM Plex Mono for code, preserving licenses and using `font-display: swap`. See [IBM Plex](https://github.com/IBM/plex).
- **Light palette:** background `#F5F7FB`, panels `#FFFFFF`, text `#182230`, secondary text `#586579`, borders `#DCE2EB`, accent `#4338CA`.
- **Dark palette:** background `#11141D`, panels `#1B2030`, text `#EEF1FA`, secondary text `#B6BED1`, borders `#383F54`, accent `#AAA5FF`.
- **Product accents:** indigo for Praxis, muted plum for Praxis AI, and amber for Policy, accompanied by names and symbols.
- **Reading:** 18px article text, 16px interface text, approximately 1.7 article line height, and a maximum paragraph width of 72 characters. Reference tables can use additional width.
- **Motion:** restrained interaction transitions with reduced-motion support.

Use a consistent heading scale, spacing rhythm, and restrained borders. Treat the explanatory architecture graphic as the principal visual feature.

The header contains Products, Docs, Community, Get started, Search, appearance selection, and GitHub. Product entries include explanatory subtitles so readers can distinguish the Praxis ecosystem name from the proxy framework.

Mobile navigation retains visible search and appearance controls. Documentation navigation becomes a drawer, and the table of contents becomes an expandable “On this page” control, using the existing theme and Bootstrap behavior where suitable.

Replace the empty footer with useful product, documentation, and contribution links. Add favicons, social previews derived from the vector identity, descriptive page metadata, and a helpful 404 page.

### Homepage structure

The ecosystem homepage remains a Hugo landing page. Its purpose is orientation and product discovery.

1. **Hero:** “Build, route, and govern application traffic.” Explain the three products briefly. Actions: **Get started** and **Browse documentation**.
2. **Ecosystem diagram:** show the proxy framework, Praxis AI's relationship to it, and the independently versioned Policy component. Label optional integrations.
3. **Choose a task:** “Build a proxy,” “Route AI traffic,” and “Enforce policy,” each linking directly to the relevant default-release starting point.
4. **Product overview:** concise capability descriptions, catalog-derived release labels, maturity badges, and deeper product links.
5. **Continue learning:** routes into tutorials, how-to guides, reference, and explanation, followed by contribution links.

Use a deliberate product order: Praxis, Praxis AI, Policy. Give the hero, diagram, task entries, and product comparison different layouts suited to their information. Repository links are secondary actions.

An overview should explain the area and where to start before routing readers onward. See [Cloudflare overview guidance](https://developers.cloudflare.com/style-guide/documentation-content-strategy/content-types/overview/).

Show product relationships without implying that every deployment chains all three products, or that independently published versions form a tested compatibility combination. Keep maturity descriptions consistent with the selected product documentation.

Add these public routes:

| Route | Purpose |
| --- | --- |
| `/start/` | Choose a task, understand prerequisites, and reach the appropriate starting guide |
| `/docs/` | Browse documentation by product and Diátaxis reader need |
| `/search/` | Search with shareable query and scope state |

Keep `/praxis/`, `/ai/`, and `/policy/` as product overview routes. Give each an introduction, explanatory visual, prominent starting action, maturity information, and useful Diátaxis entry points. Remove repetitive automatic version listings from their main content.

Examples remain tied to authoritative release documentation. Introduce prerequisites before displaying copyable commands. Record missing prerequisites or factual corrections as upstream follow-ups.

Expand Community into explicit routes for help, issues, contributions, and ecosystem proposals.

### Recommended skills

| Skill | Role | Recommendation |
| --- | --- | --- |
| [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Visual direction, typography, composition, and screenshot critique | Primary creative skill; apply its guidance to Hugo templates and SCSS |
| [Vercel web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | Interface, accessibility, responsiveness, and performance review | Review each completed phase |
| [OpenAI playwright](https://github.com/openai/skills/tree/main/skills/.curated/playwright) | Browser screenshots and interaction verification | Use for desktop, mobile, keyboard, search, and theme checks |
| [Impeccable](https://github.com/pbakaus/impeccable) | A broader workflow for critique, typography, adaptation, and polish | Optional alternative for ongoing design work; includes additional tooling |

Use the first three as the recommended combination. Skill installation remains separate from website dependencies. The research initially installed no UI skills. On 2026-09-30, the user requested installation and application of the first three; see [ui-skill-provenance.json](ui-skill-provenance.json) for exact revisions and [skill-guided-revision.md](skill-guided-revision.md) for their application.

Record selected skill repository revisions and provenance when installing them. Pin executable QA tools separately from skill instructions. The CLI Playwright skill is the default recommendation for this environment; the interactive variant requires capabilities that were not available during this audit.

## 4. Documentation reading, search, diagrams, and versions

### Article presentation

Update the existing shared adapter in `tools/docs.py` to normalize repeated leading headings while preserving anchors, derive meaningful summaries, and attach navigation metadata.

Retain Docsy article layouts, breadcrumbs, table of contents, highlighting, and copy controls. Improve their typography, spacing, active states, notices, and mobile presentation. Keep scrolling for wide tables and long code contained within those elements.

Make related links intentional across Diátaxis forms: a tutorial can point to the relevant reference and explanation; a how-to can link to the concepts behind its procedure.

Consolidate source and contribution controls. View-source links identify the exact snapshot and original mapped file. Edit actions appear only where a valid contributor target exists. Website-owned pages target the website repository.

Display product/version context beside navigation. Preserve the corresponding source page during version switching when available; otherwise open the selected version's overview with an explicit fallback notice. Keep archive and development banners visible.

### Search

Retain local Lunr. Add an accessible native search dialog and the dedicated search page:

- Search is visible throughout the site, with `Ctrl/Cmd+K`, Escape, and focus restoration.
- General site search defaults to all products' default releases.
- Product documentation search defaults to the selected product/version.
- Selecting all products searches default releases; historical and development documentation remains available through explicit product/version selection.
- Provide product, version, and **documentation-form** filters.
- Results show title, useful snippet, product/version, and reader need.
- Prioritize title and heading matches over body matches.
- Load indexes on demand and reuse them during the session.
- Include loading, empty, unavailable, and retry states.

Extend the current index with reader need, product, version, topic, and headings. Generate a small mapping from search scope to index URL. Share searches through `/search/` query parameters, including the query, product, version, and selected documentation form.

Keep normal documentation navigation usable independently of search loading.

### Diagrams and publication

Use a static accessible SVG ecosystem diagram on the homepage. Reuse existing versioned diagrams in product overviews where relevant.

Retain Docsy's pinned Mermaid integration. Add consistent framing, readable sizing, and an enlarged view using a native dialog. Preserve imported SVG colors and descriptions; use a suitable canvas in dark mode. Website-authored diagrams receive captions and equivalent textual explanations.

Verify Mermaid visibility and reading position after appearance changes. Keep historical diagrams coupled to their original documentation snapshots.

Produce clean production output to prevent stale pages and search assets accumulating. Generate canonical URLs from configurable `baseURL`. General pages and default-release documentation are indexable; development and archived snapshots use `noindex,follow` while retaining their public URLs.

## 5. Implementation phases and acceptance

### Phase 1 — Foundations and Diátaxis audit

Use this document as the implementation handoff. Classify imported content, identify mixed-purpose documents and gaps, and implement identity, typography, and appearance tokens through Docsy's supported hooks.

Deliver a concise source-document classification and upstream editorial backlog alongside the visual foundations.

### Phase 2 — Orientation and navigation

Implement the homepage, onboarding, docs directory, product overviews, Community, shared header/footer, and product/version-scoped Diátaxis navigation.

Verify the new routes and the unchanged product and snapshot routes before proceeding.

### Phase 3 — Reading and discovery

Implement heading normalization, summaries, article polish, related-document links, contribution controls, version switching, search, and diagram presentation.

Complete favicons/social previews, publication metadata, archive indexing policy, and clean production output.

### Phase 4 — Validation and refinement

Review real-browser screenshots and interactions, correct visual inconsistencies, and verify:

- Each product's starting guide is reachable from the homepage within two activations.
- Readers can distinguish learning, task guidance, lookup, and conceptual material.
- Classification reflects article purpose; empty categories are omitted.
- Existing URLs, anchors, assets, source mappings, and independent versions remain valid.
- Articles have one main heading and clear product/version context.
- Representative landing, tutorial, how-to, reference, explanation, archive, and development pages work at 320, 390, 768, 1024, and 1440px widths.
- Keyboard navigation, search, appearance selection, copy controls, diagrams, and version switching work correctly.
- Contrast, focus, zoom/reflow, touch targets, and diagram descriptions meet the intended WCAG 2.2 AA requirements. Regular text has at least 4.5:1 contrast, with reflow at 320 CSS pixels and contained scrolling for necessary code, tables, and diagrams. See [contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) and [reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).
- Browser inspection and isolated accessibility scans complement manual review. See [Playwright accessibility guidance](https://playwright.dev/docs/accessibility-testing). Automated accessibility scanning requires separate tooling such as axe; it is not a native capability of Playwright alone.
- Search loads on demand; added custom JavaScript stays below 20 KB compressed.
- Loading/layout stability targets are LCP ≤2.5 seconds and CLS ≤0.1 on a repeatable mobile profile. These are implementation targets, not measurements established by the initial audit. See [Web Vitals](https://web.dev/articles/vitals).
- `make build` and `make check` pass, alternate configured domains work, and source worktrees remain unchanged.

### Required defaults and handoff

Continue using Hugo and Docsy. Preserve the Docker workflow and configurable domain. Apply Diátaxis incrementally, keep product content authoritative upstream, and use native features and existing dependencies before adding tooling.

Browser QA tooling stays outside the website's production dependencies. Keep dependency pins and audit results reviewable.

The implementation report should identify completed phases, representative browser evidence, executed checks, preserved source worktree state, any unresolved upstream content gaps, and any external publishing action still awaiting authorization.
