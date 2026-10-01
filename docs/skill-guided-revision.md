# Skill-guided website revision

Date: 2026-09-30. This revision responds to the user's rejection of the first implementation's colors, type scale, layout roughness, and developer-first filter guidance. Hugo, Docsy, Diátaxis, independent release snapshots, and Docker build/serve remain the foundation.

## Skills actually installed and applied

- **frontend-design**: two-pass design direction and critique, cool-neutral/indigo tokens, restrained hierarchy, plain user-oriented copy, and visual screenshot review. The design notes are retained below.
- **web-design-guidelines**: fetched official rules and audited layout, native controls, focus, dark theme, readable content, and accessibility. Corrected theme initialization cleanup, header search dialog semantics, source-link new-tab announcements, and navigation landmark labels.
- **playwright**: used the installed CLI wrapper to open Chrome, take snapshots before referenced clicks, open the mobile menu, navigate, inspect computed typography, and capture desktop/mobile screenshots. Existing isolated Playwright/axe scripts supplement the CLI review.

All three are installed in the user's Codex skill directory, separate from website npm dependencies. Exact repository revisions and guideline digest are in [ui-skill-provenance.json](ui-skill-provenance.json). Markdown security scans found no flagged instructions. The Playwright shell wrapper was also read before execution. Codex automatically discovers the new skills on the next turn; this revision read and applied their installed instructions explicitly.

## Design decisions

- Light surfaces: cool paper `#F5F7FB`, white panels, slate text `#182230`, secondary text `#586579`, borders `#DCE2EB`, indigo actions `#4338CA`.
- Dark surfaces: `#11141D`, panels `#1B2030`, text `#EEF1FA`, secondary text `#B6BED1`, borders `#383F54`, soft indigo `#AAA5FF`.
- Self-hosted IBM Plex remains. Interface text is 16px; article text is 18px with 1.7 line height. Guide reading width is 48rem; guide headings use a 32–40px scale and 24–28px section headings.
- Keep the relationship diagram as the principal illustration. Use quiet surroundings, fewer decorative labels, no card hover lift, and smaller mobile hero type. Fit the complete homepage diagram on phones; enlargement retains a readable detailed view.
- Desktop header places navigation between brand and search/theme tools; mobile keeps search and theme visible beside the menu.
- Apply the accent consistently to the Praxis symbol, authored diagrams, favicon, and social preview.

The frontend-design critique rejected a generic centered hero and uniform feature-card treatment: readers need to distinguish products and configure behavior. The retained left-aligned introduction, relationship diagram, task choices, and product rows have different roles. Product status and release labels stay factual.

## End-user guidance

The new [Choose and configure filters](../content/guides/use-filters.md) guide explains filters, routes, and backends in plain terms. It includes a complete `static_response` configuration, prerequisites, validation/start commands, a curl request, and expected response details. It needs no backend or private-endpoint opt-in. Configuration fields and CLI behavior were checked against Praxis v0.7.2's pinned documentation snapshot; the product executable was not built or run during this website task.

Built-in filter configuration comes before custom Rust extension work. The homepage, start page, Praxis overview, and documentation hub expose the guide; custom filter development is clearly labelled as a developer path. How-to groups appear before tutorials in shared discovery and sidebars. Tutorial remains a Diátaxis form rather than a synonym for developer content.

The small `docs-link` shortcode resolves source paths in the catalog's current default release and fails the build for missing targets. It shows release labels, avoiding hardcoded versioned links in the new onboarding pages. When promoting a default release, maintainers must recheck the website-owned executable example against that release. Historical source prose remains unchanged.

Guide templates supply the title, article typography, native on-page navigation, and a valid website edit link. Imported documentation retains commit-pinned source actions in its article footer; an agent's initially proposed duplicate sidebar action was caught and reverted during root review.

## Validation

- Docker `make check` passed: adapter checks, presentation checks on 672 canonical pages, and 1,579 internal links including historical pages and fragments. External destination availability is outside this deterministic crawl.
- Browser checks passed on 150 page/viewport/theme combinations; 45 axe scans reported zero violations. Search, keyboard focus restoration, mobile navigation, version selection, diagram enlargement, clipboard copying, search failure/retry, and empty-result behavior passed. No JavaScript page errors were recorded.
- CLI snapshots and screenshots were reviewed for the homepage and guide, including both themes. Mobile guide computed styles are 18px body text, 30.6px line height, 32px H1, and 24px H2; document width equals the 390px viewport.
- The first integrated browser pass found dark active-TOC contrast failures. Shared Docsy tokens were corrected and the entire matrix rerun successfully. A focus assertion was updated to wait for the native dialog close event; actual focus restoration was also verified through the skill CLI.
- Three uncached mobile performance runs with gzip, 4× CPU throttling, 150ms network latency, and 1.6Mbps download measured LCP at 1.136–1.180 seconds and CLS at zero. These are local lab measurements; deployed text compression remains required. See [performance results](skill-guided-evidence/performance.json).
- Custom interaction JavaScript remains approximately 3.6 KB gzip (below the 20 KB budget). No website npm dependency was added. Product source worktrees remain unchanged.

Evidence: [browser report](skill-guided-evidence/report.json), [desktop homepage](skill-guided-evidence/home-light-1440.png), [mobile homepage](skill-guided-evidence/home-light-390.png), [dark homepage](skill-guided-evidence/home-dark-1440.png), [mobile user guide](skill-guided-evidence/user-guide-light-390.png), and [dark user guide](skill-guided-evidence/user-guide-dark-390.png). Automated scans supplement visual and keyboard review; they do not establish complete assistive-technology conformance.


## Follow-up: alignment, navigation, examples, and project wording

The user identified header overlap and column/sidebar misalignment after the initial checks. The first responsive matrix checked body overflow and accessibility but did not compare title geometry to the fixed header or column positions between rows. Those checks are now explicit.

- The default landing layout did not reserve space for Docsy’s fixed navbar at tablet/desktop widths. The original focused reproduction measured a guide title at 48px while the navbar ended at 64px. The shared default main now reserves the native navbar height at that breakpoint; documentation layouts retain their existing offset.
- Page selectors such as `.start-page` also matched the body and global header. Article scoping prevents those rules from padding or resizing the mobile navbar.
- Each ecosystem row used an independently sized `auto` action column. All rows now use identical explicit grid tracks, aligning names, descriptions, release/status information, and links.
- The redundant sidebar project/version line is removed. The article version selector remains available. Topic groups previously sorted alphabetically, putting Developing before First Proxy and Operating; per-project `topic_order` now places starting and operational topics first. Unknown future topics remain visible afterward.
- Visible ecosystem wording uses **Projects**, including the main menu, footer, search filters, overview labels, and “One ecosystem, three independent projects.” Internal catalog keys and source-authored prose retain their existing identifiers.
- Referenced textual example files render within versioned documentation, with syntax highlighting, native copy controls, exact upstream source actions, local downloads, and corresponding-page version switching. Each Examples index lists only the examples embedded for that snapshot. Default releases currently expose 32 Praxis and 3 Praxis AI example files; Policy has no linked standalone example files. The adapter renders 160 example files across all release/development snapshots. An additional check verified every downloaded file against its exact Git blob. Original product source files remain untouched.
- Deprecated data access now uses [hugo.Data](https://gohugo.io/functions/hugo/data/). Search indexes iterate each site’s [Pages](https://gohugo.io/methods/site/pages/) within `hugo.Sites`, replacing the deprecated AllPages call and avoiding duplicate language collections. The pinned Docsy files required no edits for these warnings.
- Preview and production now have separate output directories. A running older preview can overwrite `public`; the revised serve command uses `.cache/serve-public`, while checks can use an isolated destination. Restart existing `make serve` sessions to pick up this command-line change.

Final follow-up validation passed:

- Isolated Docker `make check HUGO_DESTINATION=.cache/review-public`: adapter checks, presentation checks on **840 canonical pages**, and **2,075 internal links**, with no Hugo deprecation warnings. Custom interaction JavaScript remains 3,600 bytes gzip.
- **170 responsive page/viewport/theme cases** and **53 axe scans**, with zero reported violations or JavaScript page errors. Checks include title clearance, row-column alignment, hidden sidebar context, topic order, rendered example/download equality, and example version switching.
- Final desktop visual review confirmed the removed sidebar line and embedded example layout. Product source worktrees remain unchanged.

Evidence: [follow-up browser report](skill-guided-evidence/follow-up-report.json), [light homepage](skill-guided-evidence/follow-up-home-light-1440.png), [dark homepage](skill-guided-evidence/follow-up-home-dark-1440.png), [mobile user guide](skill-guided-evidence/follow-up-user-guide-light-390.png), [desktop example](skill-guided-evidence/follow-up-example-light-1440.png), [mobile example](skill-guided-evidence/follow-up-example-light-390.png), and [sidebar ordering](skill-guided-evidence/follow-up-how-to-light-1440.png). These automated checks supplement visual review; they do not establish complete assistive-technology conformance.
