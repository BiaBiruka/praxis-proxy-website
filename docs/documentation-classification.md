# Documentation classification and editorial backlog

This audit classifies imported public articles by their main reader need. The website applies these presentation labels and summaries in generated content; product repositories remain the source of truth for prose and examples. Path-level assignments, ordering, summary overrides, and related source paths live in [`data/docs_navigation.json`](../data/docs_navigation.json).

## Current classification

Counts below cover distinct source paths selected by the current release catalog, before multiplying them across archived and development versions.

| Product | Tutorials | How-to guides | Reference | Explanation | Overview | Release |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Praxis | 1 | 13 | 40 | 16 | 2 | 1 |
| Praxis AI | 0 | 8 | 56 | 8 | 2 | 1 |
| Policy Engine | 1 | 7 | 5 | 17 | 2 | 0 |

Representative assignments:

| Product | Reader need | Examples |
| --- | --- | --- |
| Praxis | Tutorial | `docs/filters/http-filter-tutorial.md` |
|  | How-to | `docs/quickstart.md`, `docs/operating/configuration.md`, `docs/developing/adding-filters.md` |
|  | Reference | `docs/filters/reference.md` and individual filter entries |
|  | Explanation | `docs/architecture/overview.md`, `docs/filters/branch-chains.md` |
| Praxis AI | Tutorial | No current public article; this group is omitted. |
|  | How-to | `docs/quickstart.md`, `docs/developing/cli-vllm-through-praxis.md`, `docs/anthropic-messages.md` |
|  | Reference | `docs/filters/reference.md`, individual filter entries, `docs/conformance/openresponses-translation.md` |
|  | Explanation | `docs/architecture/ai-inference.md`, `docs/architecture/agentic-protocols.md` |
| Policy Engine | Tutorial | `docs/content/quickstart.md` |
|  | How-to | `docs/content/identity-claim-mapping.md`, `docs/content/identity-delegation.md` |
|  | Reference | `docs/content/apl/apl-grammar.md`, `docs/content/configuration.md` |
|  | Explanation | `docs/content/overview.md`, `docs/content/threat-model.md`, APL concept pages |

Product documentation indexes keep the `Overview` role, and release-process pages keep the `Release` role. Those pages do not appear as empty Diátaxis categories. Praxis and Policy Engine have tutorials; Praxis AI has no current tutorial, so that group is omitted and recorded below. Each need group appears only when its selected version contains articles. Older snapshots use the same source-path assignments; newly encountered historic paths get a conservative path-based classification and a derived topic.

Summaries are derived from the first useful prose paragraph, with website-owned overrides for pages whose opening text is a command or otherwise weak in search and navigation. Related pages resolve by original source path within the selected product and version. A missing related page is omitted.

## Upstream editorial backlog

These are proposals for the owning product repositories. No source prose, examples, generators, or build systems were changed for this audit.

| Priority | Source path | Current primary form | Suggested upstream improvement |
| --- | --- | --- | --- |
| High | Praxis `docs/quickstart.md` | How-to guide | Keep one task-focused proxy setup path. Move the quick test-server commands into a short developer recipe, state build/toolchain prerequisites, and show the expected result after routing to the backend. |
| High | Praxis `docs/operating/configuration.md` | How-to guide | This long page combines operational tasks with a broad configuration reference. Split common operator tasks from the complete key/behavior lookup, link the task guides to that reference, and preserve the current anchors when moving sections. |
| High | Praxis AI `docs/quickstart.md` | How-to guide | State build requirements and that `OPENAI_API_KEY` must be set before the copyable request. Keep the current single route-to-backend task and expected response. |
| Medium | Praxis AI `docs/anthropic-messages.md` | How-to guide | Separate the native-backend and translation procedures into focused task guides. Move filter contracts into the filter reference, and identify prerequisites and expected outcomes for each runnable example. |
| Medium | Praxis AI documentation set | Missing tutorial | Add a beginner learning sequence with a bounded outcome and explicit expected results; the current `quickstart.md` is a concise task recipe and remains in How-to guides. |
| Medium | Policy Engine `docs/content/identity-delegation.md` | How-to guide | Keep one task-focused setup path, then link the delegation concepts and full configuration details to their own explanation and reference pages. Make the assumptions for each principal recipe explicit. |

The Policy Engine quickstart already has a bounded scenario, prerequisites, runnable steps, expected outcomes, and clear next links. Its overview explains the enforcement model through examples, so it remains an Explanation rather than being reclassified as a tutorial.
