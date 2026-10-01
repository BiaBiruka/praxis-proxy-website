#!/usr/bin/env python3
"""Acquire and adapt the pinned product documentation for Hugo."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
CACHE = ROOT / ".cache"
DOCS_OUT = CACHE / "docs"
DATA_OUT = CACHE / "docs-data"
STATIC_OUT = CACHE / "docs-static"
CATALOG = ROOT / "data" / "docs_versions.json"
NAVIGATION = ROOT / "data" / "docs_navigation.json"
RELEASE_TAG = re.compile(r"v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?\Z")
GIT_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
GIT_SHA = re.compile(r"[0-9a-fA-F]{40}\Z")
LINK = re.compile(r"(?P<start>!?\[[^\]]*\]\()(?P<url><[^>]+>|[^\s)]+)(?P<end>[^)]*\))")
REFERENCE_DEFINITION = re.compile(
    r"(?m)^(?P<prefix>[ \t]{0,3}\[(?:\\.|[^\]])+\]:[ \t]*)"
    r"(?P<url><[^>\r\n]+>|[^\s]+)(?P<suffix>[^\r\n]*)(?P<newline>\r?\n|$)"
)
HTML_LINK = re.compile(r"(?P<attr>\b(?:href|src)=['\"])(?P<url>[^'\"]+)(?P<end>['\"])", re.I)
HTML_ELEMENT = re.compile(r"<[A-Za-z][A-Za-z0-9:-]*\b[^<>]*>", re.S)
HEADING = re.compile(r"^#\s+(.+?)\s*#*\s*$", re.M)
INLINE_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)|!?\[([^\]]*)\]\[[^]]*\]")
HTML_TAG = re.compile(r"<[^>]*>")
ARTICLE_NEEDS = ("How-to", "Tutorial", "Reference", "Explanation")
OTHER_NEEDS = ("Overview", "Release")
EXAMPLE_SUFFIXES = {".yaml", ".yml", ".json", ".toml", ".conf", ".ini", ".xml", ".sh", ".py", ".rs"}


def run(args: list[str], *, cwd: Path = ROOT, capture: bool = False) -> str:
    result = subprocess.run(
        args, cwd=cwd, text=True, stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None, check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() if capture and result.stderr else ""
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}{': ' + detail if detail else ''}")
    return result.stdout.strip() if capture and result.stdout else ""


def catalog() -> dict:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    for product, config in data["products"].items():
        releases = config["releases"]
        versions = [release["version"] for release in releases]
        tags = [release["tag"] for release in releases]
        if len(versions) != len(set(versions)) or len(tags) != len(set(tags)):
            raise RuntimeError(f"{product} catalog contains duplicate versions or tags")
        if sum(release["default"] for release in releases) != 1:
            raise RuntimeError(f"{product} catalog must mark exactly one release as default")
        default = next(release for release in releases if release["default"])
        if config["default"] != default["version"]:
            raise RuntimeError(f"{product} default does not match its marked release")
        for release in releases:
            if not RELEASE_TAG.fullmatch(release["tag"]) or not GIT_SHA.fullmatch(release["sha"]):
                raise RuntimeError(f"{product} {release['version']} must have a release tag and full commit SHA")
    return data


def git(repo: Path, *args: str) -> str:
    return run(["git", "-C", str(repo), *args], capture=True)


def repository_url(product: str) -> str:
    url = run(["git", "config", "--file", str(ROOT / ".gitmodules"), "--get",
               f"submodule.sources/{product}.url"], capture=True)
    return url.removesuffix(".git")


def pointer(product: str) -> str:
    output = run(["git", "ls-files", "-s", "--", f"sources/{product}"], capture=True)
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[0] == "160000":
            return fields[1]
    raise RuntimeError(f"sources/{product} is not recorded as a Git submodule in the index")


def source_state(product: str) -> tuple[str, str, str]:
    repo = SOURCES / product
    commit = git(repo, "rev-parse", "HEAD")
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    branch = git(repo, "branch", "--show-current")
    return commit, status, branch


def check_catalog_objects(*, fetch: bool) -> None:
    data = catalog()["products"]
    for product, config in data.items():
        repo = SOURCES / product
        for release in config["releases"]:
            tag = release["tag"]
            exists = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            ).returncode == 0
            if not exists and fetch:
                run(["git", "-C", str(repo), "fetch", "--depth=1", "origin", f"refs/tags/{tag}:refs/tags/{tag}"])
            if not exists and not fetch:
                raise RuntimeError(f"missing {product} release tag {tag}; run make init")
            actual = git(repo, "rev-parse", f"{tag}^{{commit}}")
            if actual != release["sha"]:
                raise RuntimeError(f"{product} {tag} resolved to {actual}, catalog records {release['sha']}")


def init() -> None:
    for product in catalog()["products"]:
        path = SOURCES / product
        if not (path / ".git").exists():
            run(["git", "submodule", "update", "--init", "--depth", "1", "--", f"sources/{product}"])
    check_catalog_objects(fetch=True)
    print("Source submodules and cataloged release objects are ready.")


def selected_files(repo: Path, config: dict) -> list[Path]:
    chosen: set[Path] = set()
    for pattern in config["include"]:
        if pattern.endswith("/**"):
            base = repo / pattern[:-3]
            if base.exists():
                chosen.update(path for path in base.rglob("*") if path.is_file())
        else:
            path = repo / pattern
            if path.is_file():
                chosen.add(path)
    for required in config["required"]:
        if not (repo / required).is_file():
            raise RuntimeError(f"required {required} is missing from {repo.name} snapshot")
    return sorted(chosen)


def archived_source(repo: Path, sha: str, config: dict, destination: Path) -> None:
    roots = sorted({pattern[:-3] for pattern in config["include"] if pattern.endswith("/**")})
    exact = [pattern for pattern in config["include"] if not pattern.endswith("/**")]
    paths = [path for path in roots + exact if subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{sha}:{path}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0]
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", sha, "--", *paths],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if archive.returncode:
        raise RuntimeError(archive.stderr.decode("utf-8", "replace").strip())
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(fileobj=__import__("io").BytesIO(archive.stdout), mode="r:") as bundle:
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            if root not in target.parents and target != root:
                raise RuntimeError(f"unsafe path in Git archive: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is not None:
                    target.write_bytes(source.read())


def site_url(product: str, version: str, output_path: str) -> str:
    path = PurePosixPath(output_path)
    if path.name == "_index.md":
        relative = path.parent.as_posix()
        suffix = "" if relative == "." else relative + "/"
    else:
        suffix = path.with_suffix("").as_posix() + "/"
    return f"/{product}/{version}/{suffix}"


def normalized_repo_path(source_path: str, href_path: str) -> str | None:
    if href_path.startswith("/"):
        return None
    path = PurePosixPath(source_path).parent.joinpath(PurePosixPath(href_path))
    parts: list[str] = []
    for part in path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


def read_blob(repo: Path, sha: str, rel: str, *, working: bool) -> bytes | None:
    path = repo / rel
    if working and path.is_file():
        return path.read_bytes()
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{sha}:{rel}"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def repo_paths(repo: Path, sha: str, *, working: bool) -> set[str]:
    paths = set(git(repo, "ls-tree", "-r", "--name-only", sha).splitlines())
    if working:
        paths.update(git(repo, "ls-files", "--cached", "--others", "--exclude-standard").splitlines())
    return paths


def markdown_links(text: str):
    """Yield Markdown and HTML link targets outside code, comments, and escaped links."""
    chunk: list[str] = []
    fence: str | None = None
    fence_length = 0

    def targets(value: str):
        masked, _ = _protect_non_markdown(value)
        for match in REFERENCE_DEFINITION.finditer(masked):
            yield match.group("url").strip("<>")
        for match in LINK.finditer(masked):
            if not _is_escaped(masked, match.start("start")):
                yield match.group("url").strip("<>")
        for element in HTML_ELEMENT.finditer(masked):
            for match in HTML_LINK.finditer(element.group(0)):
                yield match.group("url")

    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)[0]
            if fence is None:
                yield from targets("".join(chunk))
                chunk.clear()
                fence = token
                fence_length = len(marker.group(1))
            elif token == fence and len(marker.group(1)) >= fence_length:
                fence = None
                fence_length = 0
            continue
        if fence is None:
            chunk.append(line)
    yield from targets("".join(chunk))


def linked_examples(source_files: list[Path], source_root: Path, *, repo: Path, sha: str,
                    working: bool, known_paths: set[str]) -> tuple[dict[str, str], set[str], dict[str, str]]:
    """Load only textual examples linked by selected Markdown pages."""
    paths: set[str] = set()
    directories: set[str] = set()
    for source_file in source_files:
        if source_file.suffix.lower() != ".md":
            continue
        source_path = source_file.relative_to(source_root).as_posix()
        for raw in markdown_links(source_file.read_text(encoding="utf-8")):
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = normalized_repo_path(source_path, unquote(parts.path))
            if not target or not target.startswith("examples/"):
                continue
            if target == "examples/README.md" and target in known_paths:
                paths.add(target)
            elif PurePosixPath(target).suffix.lower() in EXAMPLE_SUFFIXES and target in known_paths:
                paths.add(target)
            elif not PurePosixPath(target).suffix and any(
                path.startswith(target.rstrip("/") + "/") for path in known_paths
            ):
                directories.add(target.rstrip("/"))

    examples: dict[str, str] = {}
    for path in sorted(paths):
        body = read_blob(repo, sha, path, working=working)
        if body is None:
            continue
        try:
            value = body.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if "\0" not in value:
            examples[path] = value

    descriptions: dict[str, str] = {}
    readme = read_blob(repo, sha, "examples/README.md", working=working)
    if readme is not None:
        for line in readme.decode("utf-8", "replace").splitlines():
            match = re.match(r"^\s*\|\s*\[[^]]+\]\(([^)]+)\)\s*\|\s*(.*?)\s*\|\s*$", line)
            if match:
                target = normalized_repo_path("examples/README.md", match.group(1))
                if target and target.startswith("examples/"):
                    descriptions[target] = plain_text(match.group(2))
    return examples, directories, descriptions


def example_content_path(source_path: str) -> str:
    return "examples/_index.md" if source_path == "examples/README.md" else source_path + ".md"


def write_example_pages(product: str, version: str, label: str, sha: str, config: dict,
                        examples: dict[str, str], directories: set[str], descriptions: dict[str, str],
                        known_paths: set[str], assets: Path,
                        working: bool, source_status: str,
                        edit_branch: str) -> list[dict]:
    if not examples and not directories:
        return []
    readme_path = "examples/README.md"
    output_paths = {path: example_content_path(path) for path in examples}
    output_paths[readme_path] = "examples/_index.md"

    readme_exists = "examples/README.md" in known_paths
    samples = [(path, content) for path, content in sorted(examples.items()) if path != readme_path]
    index_lines = [
        "Examples linked from the project documentation. Each file has a version-pinned page and download.",
        "",
    ]
    for source_path, _ in samples:
        relative = PurePosixPath(source_path).relative_to("examples").as_posix()
        detail = descriptions.get(source_path, "")
        link = site_url(product, version, output_paths[source_path])
        index_lines.append(f"- [`{relative}`]({link})" + (f" — {detail}" if detail else ""))
    index_body = "\n".join(index_lines) + "\n"

    output: list[dict] = []
    product_name = config["name"]
    for order, (source_path, content) in enumerate(samples, start=1000):
        output_path = output_paths[source_path]
        title = PurePosixPath(source_path).stem.replace("-", " ").replace("_", " ").title()
        category = PurePosixPath(source_path).parent.name.replace("-", " ")
        summary = descriptions.get(source_path) or f"Configuration example in {category} for {product_name}."
        if len(summary) < 20:
            summary = f"{summary} Example configuration for {product_name}."
        download_path = f"{product}/{version}/_assets/{source_path}"
        download_file = assets / download_path
        download_file.parent.mkdir(parents=True, exist_ok=True)
        download_file.write_bytes(content.encode("utf-8"))
        download = f"/{download_path}"
        fence_length = max((len(match.group(0)) for match in re.finditer(r"`+", content)), default=2) + 1
        fence = "`" * max(3, fence_length)
        language = PurePosixPath(source_path).suffix.removeprefix(".")
        page_body = f"Download the [source file]({download}).\n\n{fence}{language}\n{content}"
        if not content.endswith("\n"):
            page_body += "\n"
        page_body += f"{fence}\n"

        destination = DOCS_OUT / product / version / output_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        path_base = {
            "from": "^" + re.escape(f".cache/docs/{product}/{version}/{output_path}") + "$",
            "to": source_path,
        }
        metadata = {
            "title": title, "product": product, "version": version, "version_label": label,
            "source_commit": sha, "source_repo": config["repo"], "source_path": source_path,
            "issue_url": config["issues"], "version_archive": version != "dev" and version != config["default"],
            "github_repo": config["repo"], "github_branch": sha, "github_project_repo": config["repo"],
            "github_subdir": "", "path_base_for_github_subdir": path_base,
            "description": summary, "summary": summary, "reader_need": "Reference", "topic": "Examples",
            "order": order, "preview_dirty": bool(source_status),
        }
        if version == "dev" and edit_branch:
            metadata["edit_url"] = f"{config['repo']}/edit/{edit_branch}/{source_path}"
        destination.write_text(
            frontmatter(metadata) + "{{< docs-version >}}\n\n" + page_body + "\n{{< docs-source-links >}}\n",
            encoding="utf-8",
        )
        output.append({"product": product, "version": version, "source_path": source_path,
                       "content_path": output_path, "source_commit": sha,
                       "url": site_url(product, version, output_path), "dirty": bool(source_status)})

    output_path = "examples/_index.md"
    index_source = readme_path if readme_exists else "examples"
    count = len(samples)
    summary = f"Browse {count} example files linked from {product_name} documentation."
    metadata = {
        "title": "Examples", "product": product, "version": version, "version_label": label,
        "source_commit": sha, "source_repo": config["repo"], "source_path": index_source,
        "issue_url": config["issues"], "version_archive": version != "dev" and version != config["default"],
        "description": summary, "summary": summary, "reader_need": "Overview", "topic": "Examples", "order": 20,
        "no_list": True,
    }
    destination = DOCS_OUT / product / version / output_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        frontmatter(metadata) + "{{< docs-version >}}\n\n" + index_body,
        encoding="utf-8",
    )
    output.append({"product": product, "version": version, "source_path": index_source,
                   "content_path": output_path, "source_commit": sha,
                   "url": site_url(product, version, output_path), "dirty": bool(source_status)})
    return output


def map_product_doc(config: dict, source_path: str) -> str | None:
    allowed = any(source_path == pattern or (pattern.endswith("/**") and source_path.startswith(pattern[:-2]))
                  for pattern in config["include"])
    if not allowed or not source_path.endswith(".md"):
        return None
    relative = PurePosixPath(source_path).relative_to(PurePosixPath(config["content_root"]))
    if source_path in config.get("indexes", []):
        return (relative.parent / "_index.md").as_posix()
    return relative.as_posix()


def rewrite_cross_product(raw: str) -> str:
    parts = urlsplit(raw)
    if parts.netloc.lower() != "github.com":
        return raw
    fields = parts.path.strip("/").split("/")
    if len(fields) < 5 or fields[0] != "praxis-proxy" or fields[2] != "blob":
        return raw
    products = catalog()["products"]
    product = fields[1]
    if product not in products:
        return raw
    config = products[product]
    ref = fields[3]
    version = ref if any(release["version"] == ref for release in config["releases"]) else config["default"]
    mapped = map_product_doc(config, "/".join(fields[4:]))
    if mapped is None:
        return raw
    return urlunsplit(("", "", site_url(product, version, mapped), parts.query, parts.fragment))


def rewrite_target(raw_url: str, *, image: bool, product: str, version: str, config: dict,
                   repo: Path, sha: str, source_path: str, selected: dict[str, str],
                   assets: Path, working: bool, known_paths: set[str]) -> str:
    wrapped = raw_url.startswith("<") and raw_url.endswith(">")
    raw = raw_url[1:-1] if wrapped else raw_url
    parts = urlsplit(raw)
    if parts.scheme or parts.netloc:
        rewritten = rewrite_cross_product(raw)
        return f"<{rewritten}>" if wrapped else rewritten
    if not parts.path or parts.path.startswith("/"):
        return raw_url
    target = normalized_repo_path(source_path, unquote(parts.path))
    if target is None:
        return raw_url
    if not image and target in selected:
        new = site_url(product, version, selected[target])
        return urlunsplit(("", "", new, parts.query, parts.fragment))
    if image and target in known_paths:
        body = read_blob(repo, sha, target, working=working)
        if body is not None:
            output = assets / product / version / "_assets" / target
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(body)
            new = f"/{product}/{version}/_assets/{target}"
            return urlunsplit(("", "", new, parts.query, parts.fragment))
    is_directory = target.endswith("/") or any(path.startswith(target.rstrip("/") + "/") for path in known_paths)
    ref_type = "tree" if is_directory else "blob"
    source_url = f"{config['repo']}/{ref_type}/{sha}/{quote(target, safe='/')}"
    return urlunsplit(("", "", source_url, parts.query, parts.fragment))


def _is_escaped(text: str, position: int) -> bool:
    slashes = 0
    position -= 1
    while position >= 0 and text[position] == "\\":
        slashes += 1
        position -= 1
    return slashes % 2 == 1


def _protect_non_markdown(text: str) -> tuple[str, dict[str, str]]:
    """Mask inline code and HTML comments while rewriting links in Markdown text."""
    masked: list[str] = []
    protected: dict[str, str] = {}
    cursor = 0

    def mask(value: str) -> str:
        token = f"\x00DOCS-LITERAL-{len(protected)}\x00"
        protected[token] = value
        return token

    while cursor < len(text):
        comment_start = text.find("<!--", cursor)
        tick_start = text.find("`", cursor)
        while tick_start >= 0 and _is_escaped(text, tick_start):
            tick_start = text.find("`", tick_start + 1)
        if comment_start < 0 and tick_start < 0:
            masked.append(text[cursor:])
            break

        if comment_start >= 0 and (tick_start < 0 or comment_start < tick_start):
            comment_end = text.find("-->", comment_start + 4)
            end = len(text) if comment_end < 0 else comment_end + 3
            masked.extend((text[cursor:comment_start], mask(text[comment_start:end])))
            cursor = end
            continue

        masked.append(text[cursor:tick_start])
        run_end = tick_start + 1
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        delimiter_length = run_end - tick_start
        search = run_end
        close_start = -1
        close_end = -1
        while search < len(text):
            candidate = text.find("`", search)
            if candidate < 0:
                break
            candidate_end = candidate + 1
            while candidate_end < len(text) and text[candidate_end] == "`":
                candidate_end += 1
            if candidate_end - candidate == delimiter_length:
                close_start, close_end = candidate, candidate_end
                break
            search = candidate_end
        if close_start < 0:
            masked.append(text[tick_start:run_end])
            cursor = run_end
            continue
        masked.append(mask(text[tick_start:close_end]))
        cursor = close_end

    return "".join(masked), protected


def _rewrite_markdown_chunk(text: str, **context) -> str:
    masked, protected = _protect_non_markdown(text)

    def replace_reference(match: re.Match) -> str:
        url = match.group("url")
        rewritten = rewrite_target(url, image=False, **context)
        return match.group("prefix") + rewritten + match.group("suffix") + match.group("newline")

    masked = REFERENCE_DEFINITION.sub(replace_reference, masked)

    def replace_link(match: re.Match) -> str:
        start = match.start("start")
        if _is_escaped(masked, start):
            return match.group(0)
        raw = match.group("url")
        target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
        is_image = match.group("start").startswith("!")
        rewritten = rewrite_target(target, image=is_image, **context)
        wrapped = f"<{rewritten}>" if raw.startswith("<") and raw.endswith(">") else rewritten
        return match.group("start") + wrapped + match.group("end")

    masked = LINK.sub(replace_link, masked)

    def replace_html(match: re.Match) -> str:
        is_image = match.group("attr").lower().startswith("src")
        rewritten = rewrite_target(match.group("url"), image=is_image, **context)
        return match.group("attr") + rewritten + match.group("end")

    def replace_html_element(match: re.Match) -> str:
        return HTML_LINK.sub(replace_html, match.group(0))

    masked = HTML_ELEMENT.sub(replace_html_element, masked)
    for token, literal in protected.items():
        masked = masked.replace(token, literal)
    return masked


def rewrite_markdown(text: str, **context) -> str:
    output: list[str] = []
    markdown_chunk: list[str] = []
    fence: str | None = None
    fence_length = 0

    def flush_markdown() -> None:
        if markdown_chunk:
            output.append(_rewrite_markdown_chunk("".join(markdown_chunk), **context))
            markdown_chunk.clear()

    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)[0]
            if fence is None:
                flush_markdown()
                fence = token
                fence_length = len(marker.group(1))
                output.append(line)
            elif token == fence:
                output.append(line)
                if len(marker.group(1)) >= fence_length:
                    fence = None
                    fence_length = 0
            else:
                output.append(line)
            continue
        if fence is not None:
            output.append(line)
            continue
        markdown_chunk.append(line)
    flush_markdown()
    return "".join(output)


def adapt_page_markdown(text: str, title: str, **context) -> str:
    """Apply source-link rewrites and remove the body H1 duplicated by page metadata."""
    return remove_duplicate_initial_h1(rewrite_markdown(text, **context), title)


def quote_toml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def frontmatter(values: dict) -> str:
    lines = ["+++", f"title = {quote_toml(values['title'])}", 'type = "docs"']
    for key in ("weight", "order", "product", "version", "version_label", "source_commit", "source_repo",
                "source_path", "issue_url", "reader_need", "topic", "summary", "edit_url", "github_repo",
                "github_branch", "github_subdir", "github_project_repo", "description"):
        if key in values and values[key] is not None:
            value = values[key]
            if isinstance(value, int):
                lines.append(f"{key} = {value}")
            else:
                lines.append(f"{key} = {quote_toml(str(value))}")
    for key in ("version_archive", "preview_dirty"):
        if key in values:
            lines.append(f"{key} = {'true' if values[key] else 'false'}")
    if values.get("aliases"):
        lines.append("aliases = [" + ", ".join(quote_toml(value) for value in values["aliases"]) + "]")
    if "related_sourcepaths" in values:
        lines.append("related_sourcepaths = [" + ", ".join(quote_toml(value) for value in values["related_sourcepaths"]) + "]")
    if isinstance(values.get("path_base_for_github_subdir"), dict):
        lines.extend(["", "[path_base_for_github_subdir]"])
        for key, value in values["path_base_for_github_subdir"].items():
            lines.append(f"{key} = {quote_toml(value)}")
    elif values.get("path_base_for_github_subdir"):
        lines.append(f"path_base_for_github_subdir = {quote_toml(values['path_base_for_github_subdir'])}")
    if isinstance(values.get("cascade"), dict):
        lines.extend(["", "[cascade]"])
        for key, value in values["cascade"].items():
            lines.append(f"{key} = {'true' if value else 'false'}" if isinstance(value, bool)
                         else f"{key} = {quote_toml(str(value))}")
    lines.extend(["+++", ""])
    return "\n".join(lines)


def title_for(path: Path, text: str) -> str:
    match = HEADING.search(text)
    if match:
        return heading_text(match.group(1))
    if path.name == "_index.md":
        return "Documentation"
    return path.stem.replace("_", " ").replace("-", " ").title()


def plain_text(markdown: str) -> str:
    markdown = INLINE_LINK.sub(lambda match: match.group(1) or match.group(2) or "", markdown)
    markdown = re.sub(r"`([^`]*)`", r"\1", markdown)
    markdown = re.sub(r"[*~]", "", markdown)
    markdown = re.sub(r"(?<!\w)_(.*?)_(?!\w)", r"\1", markdown)
    markdown = HTML_TAG.sub("", markdown)
    return re.sub(r"\s+", " ", html.unescape(markdown)).strip()


def heading_text(markdown: str) -> str:
    markdown = INLINE_LINK.sub(lambda match: match.group(1) or match.group(2) or "", markdown)
    markdown = re.sub(r"`([^`]*)`", r"\1", markdown)
    markdown = re.sub(r"\s+\{#[^}]+\}\s*$", "", markdown)
    markdown = re.sub(r"[*~]", "", markdown)
    markdown = HTML_TAG.sub("", markdown)
    return re.sub(r"\s+", " ", html.unescape(markdown)).strip()


def slugify_heading(value: str) -> str:
    slug = []
    for char in heading_text(value).lower():
        if char.isalnum() or char in "-_":
            slug.append(char)
        elif char.isspace():
            slug.append("-")
    return "".join(slug)


def remove_duplicate_initial_h1(markdown: str, title: str) -> str:
    lines = markdown.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
        elif line.startswith("<!--"):
            while index < len(lines) and "-->" not in lines[index]:
                index += 1
            index += 1
        elif re.fullmatch(r"<a\s+(?:id|name)=[\"'][^\"']+[\"'][^>]*>\s*</a>", line, re.I):
            index += 1
        elif re.fullmatch(r"<img\b[^>]*?/?>", line, re.I):
            index += 1
        elif re.fullmatch(r"(?:\[)?!\[[^\]]*\]\([^)]*\)(?:\]\([^)]*\))?", line):
            index += 1
        else:
            break
    if index == len(lines):
        return markdown
    match = HEADING.fullmatch(lines[index].rstrip("\r\n"))
    if not match:
        return markdown
    heading = match.group(1).strip()
    explicit = re.search(r"\s+\{#([^}\s]+)\}\s*$", heading)
    comparable = heading[:explicit.start()].strip() if explicit else heading
    if heading_text(comparable).casefold() != heading_text(title).casefold():
        return markdown
    inline_anchor = re.search(r"<a\s+(?:id|name)=[\"']([^\"']+)[\"'][^>]*>\s*</a>", comparable, re.I)
    if explicit or inline_anchor:
        anchor = explicit.group(1) if explicit else inline_anchor.group(1)
        lines[index] = f'<a id="{anchor}"></a>\n'
    elif not any(re.search(r"(?:id|name)=[\"']", line, re.I) for line in lines[:index]):
        lines[index] = f'<a id="{slugify_heading(comparable)}"></a>\n'
    else:
        lines[index] = ""
    return "".join(lines)


def summarize(markdown: str) -> str:
    in_fence = False
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for line in markdown.splitlines():
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            if current:
                paragraphs.append(current)
                current = []
            continue
        if line.lstrip().startswith(("#", "<!--", "{{<", "|", ">", "[", "<")) or re.match(r"^\s*[-*+]\s", line):
            if current:
                paragraphs.append(current)
                current = []
            continue
        current.append(line.strip())
    if current:
        paragraphs.append(current)
    for paragraph in paragraphs:
        value = plain_text(" ".join(paragraph))
        if len(value) < 20:
            continue
        if len(value) > 200:
            sentence = re.match(r"^(.{40,200}?[.!?])(?:\s|$)", value)
            value = sentence.group(1) if sentence else value[:197].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
        return value
    return ""


def fallback_need(product: str, source_path: str) -> str:
    path = PurePosixPath(source_path)
    stem = path.stem
    parts = path.parts
    if stem == "release":
        return "Release"
    if stem in {"README", "index"}:
        return "Overview"
    if "architecture" in parts or stem in {"branch-chains", "extensions", "overview", "vision", "threat-model", "pipeline", "cmf", "cmf-extensions"}:
        return "Explanation"
    if "filters" in parts:
        if stem in {"reference"} or stem not in {"README", "extensions"}:
            return "Reference"
        return "Explanation" if stem == "extensions" else "Overview"
    if stem == "quickstart":
        return "Tutorial" if product == "policy" else "How-to"
    if "operating" in parts or "developing" in parts:
        return "How-to"
    return "Reference"


def fallback_topic(source_path: str) -> str:
    path = PurePosixPath(source_path)
    parts = [part for part in path.parts[1:-1] if part not in {"content"}]
    if parts:
        return " ".join(part.replace("_", " ").replace("-", " ").title() for part in parts)
    return "Core Concepts"


def page_metadata(product: str, source_path: str, original: str, navigation: dict) -> dict:
    product_navigation = navigation.get("products", {}).get(product, {})
    override = product_navigation.get("articles", {}).get(source_path, {})
    need = override.get("reader_need", fallback_need(product, source_path))
    if need not in (*ARTICLE_NEEDS, *OTHER_NEEDS):
        raise RuntimeError(f"invalid reader_need {need!r} for {product}:{source_path}")
    summary = override.get("summary") or summarize(original)
    if len(summary) < 20 or summary.endswith(":"):
        raise RuntimeError(f"{product}:{source_path} needs a meaningful docs_navigation summary")
    return {
        "reader_need": need,
        "topic": override.get("topic") or fallback_topic(source_path),
        "order": override.get("order", 100),
        "summary": summary,
        "related_sourcepaths": override.get("related", []),
    }


def validate_navigation(source_catalog: dict, navigation: dict) -> None:
    for product, config in source_catalog["products"].items():
        product_navigation = navigation.get("products", {}).get(product, {})
        articles = product_navigation.get("articles", {})
        if product_navigation.get("groups") != list(ARTICLE_NEEDS):
            raise RuntimeError(f"{product} docs navigation must list the four reader-need groups in order")
        if product_navigation.get("start") not in articles:
            raise RuntimeError(f"{product} docs navigation start path is not classified")
        selected = {
            path.relative_to(SOURCES / product).as_posix()
            for path in selected_files(SOURCES / product, config)
            if path.suffix.lower() == ".md"
        }
        for source_path in selected:
            metadata = articles.get(source_path)
            if metadata is None:
                raise RuntimeError(f"{product} public page lacks docs_navigation metadata: {source_path}")
            if metadata.get("reader_need") not in (*ARTICLE_NEEDS, *OTHER_NEEDS):
                raise RuntimeError(f"invalid reader_need for {product}:{source_path}")
            if not isinstance(metadata.get("topic"), str) or not metadata["topic"].strip():
                raise RuntimeError(f"{product}:{source_path} is missing its navigation topic")
            if not isinstance(metadata.get("order"), int):
                raise RuntimeError(f"{product}:{source_path} is missing its navigation order")
            for related_path in metadata.get("related", []):
                if related_path not in selected:
                    raise RuntimeError(f"{product}:{source_path} points to an unpublished related source path: {related_path}")
            summary = metadata.get("summary") or summarize((SOURCES / product / source_path).read_text(encoding="utf-8"))
            if len(summary) < 20 or summary.endswith(":"):
                raise RuntimeError(f"{product}:{source_path} needs a meaningful docs_navigation summary")


def check_adapter() -> None:
    rewrite_context = {
        "product": "praxis", "version": "dev", "config": {"repo": "https://github.com/example/docs"},
        "repo": ROOT, "sha": "0" * 40, "source_path": "docs/guide.md", "selected": {},
        "assets": ROOT / ".cache" / "check-adapter", "working": True, "known_paths": set(),
    }
    transformed = adapt_page_markdown("# Proxy setup\n\nBuild the proxy.\n", "Proxy setup")
    assert transformed.startswith('<a id="proxy-setup"></a>\n\nBuild the proxy.')
    generated = adapt_page_markdown("<!-- Generated. -->\n\n# `access_log`\n\nLogs requests.\n", "access_log")
    assert generated.startswith('<!-- Generated. -->\n\n<a id="access_log"></a>')
    badge = adapt_page_markdown(
        "![Build status](https://example.test/status.svg)\n\n# First route\n\nRun it.\n",
        "First route", **rewrite_context,
    )
    assert badge.startswith('![Build status](https://example.test/status.svg)\n\n<a id="first-route"></a>')
    comment_and_badge = adapt_page_markdown(
        '<!-- generated -->\n\n![Build status](https://example.test/status.svg)\n\n# Upgrade {#v2-to-v4}\n\nSteps.\n',
        "Upgrade", **rewrite_context,
    )
    assert comment_and_badge.endswith('<a id="v2-to-v4"></a>\n\nSteps.\n')
    assert remove_duplicate_initial_h1("# A page\n\nBody", "Different title") == "# A page\n\nBody"
    assert remove_duplicate_initial_h1("# Page {#stable-link}\n\nBody", "Page").startswith('<a id="stable-link"></a>')

    sha = "0123456789abcdef0123456789abcdef01234567"
    source_context = {
        "product": "praxis", "version": "v0.7.2",
        "config": {"repo": "https://github.com/praxis-proxy/praxis"},
        "repo": ROOT, "sha": sha, "source_path": "docs/operating/configuration.md",
        "selected": {"docs/operating/configuration.md": "operating/configuration.md"},
        "assets": ROOT / ".cache" / "check-adapter", "working": False,
        "known_paths": {"examples/configs/operations/hot-reload.yaml", "examples/configs/item.yaml"},
    }
    example_context = {
        **source_context,
        "selected": {
            **source_context["selected"],
            "examples/configs/operations/hot-reload.yaml": "examples/configs/operations/hot-reload.yaml.md",
            "examples/configs": "examples/_index.md",
        },
    }
    reference = rewrite_markdown(
        "See [hot reload][sample].\n\n[sample]: ../../examples/configs/operations/hot-reload.yaml \"Example\"\n",
        **example_context,
    )
    assert "[sample]: /praxis/v0.7.2/examples/configs/operations/hot-reload.yaml/ \"Example\"" in reference
    directory = rewrite_markdown("[examples](../../examples/configs/)\n", **example_context)
    assert "](/praxis/v0.7.2/examples/)" in directory
    html_example = rewrite_markdown('<a href="../../examples/configs/operations/hot-reload.yaml">config</a>\n', **example_context)
    assert 'href="/praxis/v0.7.2/examples/configs/operations/hot-reload.yaml/"' in html_example
    assert example_content_path("examples/configs/item.yaml") == "examples/configs/item.yaml.md"
    assert example_content_path("examples/configs/item.json") == "examples/configs/item.json.md"
    assert example_content_path("examples/configs/item.yaml") != example_content_path("examples/configs/item.json")
    raw_example = rewrite_markdown(
        f"[raw](https://github.com/praxis-proxy/praxis/blob/{sha}/examples/configs/operations/hot-reload.yaml)\n",
        **example_context,
    )
    assert f"https://github.com/praxis-proxy/praxis/blob/{sha}/examples/configs/operations/hot-reload.yaml" in raw_example
    missing_source = rewrite_markdown("[missing](../../docs/not-selected.md#part)\n", **source_context)
    assert f"https://github.com/praxis-proxy/praxis/blob/{sha}/docs/not-selected.md#part" in missing_source

    discovered = set(markdown_links(
        '[inline](sample.yaml) and [reference][sample].\n[sample]: reference.yaml\n'
        '<a href="html.yaml">example</a> ` [code](inline.yaml) `\n'
        '<!-- [comment](comment.yaml) -->\n```markdown\n[fence](fence.yaml)\n```\n'
    ))
    assert discovered == {"sample.yaml", "reference.yaml", "html.yaml"}

    policy_context = {
        **source_context, "product": "policy", "version": "v0.4.0",
        "config": {"repo": "https://github.com/praxis-proxy/policy"},
        "source_path": "docs/content/apl/attributes.md",
        "selected": {"docs/content/extensions.md": "extensions.md"},
    }
    multiline = rewrite_markdown(
        "See [Extensions &\nCapability-Gating](../extensions.md#capabilities).\n",
        **policy_context,
    )
    assert "](/policy/v0.4.0/extensions/#capabilities)" in multiline
    html_link = rewrite_markdown('<a href="../extensions.md#capabilities">read</a>\n', **policy_context)
    assert 'href="/policy/v0.4.0/extensions/#capabilities"' in html_link
    escaped_html = '&lt;a href="../extensions.md#capabilities"&gt;read&lt;/a&gt;\n'
    assert rewrite_markdown(escaped_html, **policy_context) == escaped_html
    html_comment = '<!-- <a href="../extensions.md#capabilities">comment</a> -->\n'
    assert rewrite_markdown(html_comment, **policy_context) == html_comment
    literal_paths = "`[example](../../examples/configs/item.yaml)` and \\[escaped](../../examples/configs/item.yaml).\n"
    assert rewrite_markdown(literal_paths, **source_context) == literal_paths
    fenced_paths = "```markdown\n[example](../../examples/configs/item.yaml)\n```\n"
    assert rewrite_markdown(fenced_paths, **source_context) == fenced_paths

    assert summarize("# Title\n\nA useful summary with `code` and [a link](https://example.test).\n") == "A useful summary with code and a link."
    assert slugify_heading("Dependency Policy & Review") == "dependency-policy--review"


def prepare(mode: str) -> None:
    source_catalog = catalog()
    navigation = json.loads(NAVIGATION.read_text(encoding="utf-8"))
    if mode == "build":
        check_catalog_objects(fetch=False)
    validate_navigation(source_catalog, navigation)
    for path in (DOCS_OUT, DATA_OUT, STATIC_OUT, CACHE / "source"):
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)

    products_out: dict = {}
    source_map: list[dict] = []
    for product, config in source_catalog["products"].items():
        config = {**config, "repo": repository_url(product)}
        config["issues"] = config["repo"] + "/issues/new"
        repo = SOURCES / product
        expected = pointer(product)
        source_commit, source_status, branch = source_state(product)
        if mode == "build":
            if source_commit != expected:
                raise RuntimeError(f"{product} checkout is {source_commit}, but website records {expected}; review and update the submodule pointer")
            if source_status:
                raise RuntimeError(f"{product} source checkout is dirty:\n{source_status}\nCommit or discard source changes before make build; use make serve to preview edits.")

        versions = []
        releases = config["releases"]
        default_release = config["default"]
        for release in releases:
            version = release["version"]
            sha = release["sha"]
            extracted = CACHE / "source" / product / version
            shutil.rmtree(extracted, ignore_errors=True)
            archived_source(repo, sha, config, extracted)
            selected_source = selected_files(extracted, config)
            mapping: dict[str, str] = {}
            for source_file in selected_source:
                source_rel = source_file.relative_to(extracted).as_posix()
                if source_file.suffix.lower() != ".md":
                    continue
                content_root = PurePosixPath(config["content_root"])
                relative = PurePosixPath(source_rel).relative_to(content_root)
                if source_rel in config.get("indexes", []):
                    output_path = (relative.parent / "_index.md").as_posix()
                else:
                    output_path = relative.as_posix()
                mapping[source_rel] = output_path
            known_paths = repo_paths(repo, sha, working=False)
            examples, example_dirs, example_descriptions = linked_examples(
                selected_source, extracted, repo=repo, sha=sha, working=False, known_paths=known_paths,
            )
            mapping.update({
                path: example_content_path(path)
                for path in examples
            })
            if examples or example_dirs:
                mapping["examples"] = "examples/_index.md"
                mapping["examples/README.md"] = "examples/_index.md"
                mapping.update({path: "examples/_index.md" for path in example_dirs})
            for source_file in selected_source:
                source_rel = source_file.relative_to(extracted).as_posix()
                if source_file.suffix.lower() != ".md":
                    continue
                output_path = mapping[source_rel]
                destination = DOCS_OUT / product / version / output_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                original = source_file.read_text(encoding="utf-8")
                page_body = adapt_page_markdown(
                    original, product=product, version=version, config=config, repo=repo, sha=sha,
                    title=title_for(source_file, original), source_path=source_rel, selected=mapping,
                    assets=STATIC_OUT, working=False, known_paths=known_paths,
                )
                aliases = []
                if version == default_release:
                    aliases.append(site_url(product, "latest", output_path))
                source_mount = re.escape(f".cache/docs/{product}/{version}/")
                path_base = (
                    {"from": "^" + source_mount + re.escape(output_path) + "$", "to": source_rel}
                    if source_rel in config.get("indexes", []) else
                    {"from": "^" + source_mount, "to": config["content_root"] + "/"}
                )
                content_metadata = page_metadata(product, source_rel, original, navigation)
                metadata = {
                    "title": title_for(source_file, original), "product": product, "version": version,
                    "version_label": release["label"], "source_commit": sha,
                    "source_repo": config["repo"], "source_path": source_rel,
                    "issue_url": config["issues"], "version_archive": version != default_release,
                    "github_repo": config["repo"], "github_branch": sha,
                    "github_project_repo": config["repo"],
                    "github_subdir": "",
                    "path_base_for_github_subdir": path_base,
                    "description": content_metadata["summary"],
                    **content_metadata,
                    "aliases": aliases,
                    "cascade": {
                        "product": product, "version": version, "version_label": release["label"],
                        "source_commit": sha, "version_archive": version != default_release,
                    },
                }
                shortcode = "{{< docs-version >}}\n\n{{< docs-mobile-toc >}}\n\n"
                destination.write_text(
                    frontmatter(metadata) + shortcode + page_body
                    + "\n\n{{< docs-source-links >}}\n\n{{< docs-related >}}\n",
                    encoding="utf-8",
                )
                entry = {"product": product, "version": version, "source_path": source_rel,
                         "content_path": output_path, "source_commit": sha, "url": site_url(product, version, output_path)}
                source_map.append(entry)
            source_map.extend(write_example_pages(
                product, version, release["label"], sha, config, examples, example_dirs,
                example_descriptions, known_paths, STATIC_OUT, False, "", "",
            ))
            versions.append({"slug": version, "label": release["label"], "tag": release["tag"],
                             "sha": sha, "default": release["default"]})

        working = mode == "serve"
        dev_sha = source_commit if working or not source_status else expected
        dev_label = f"Development ({dev_sha[:12]})"
        version = "dev"
        source_files = selected_files(repo, config)
        known_paths = repo_paths(repo, source_commit, working=True)
        mapping = {}
        for source_file in source_files:
            source_rel = source_file.relative_to(repo).as_posix()
            if source_file.suffix.lower() != ".md":
                continue
            relative = PurePosixPath(source_rel).relative_to(PurePosixPath(config["content_root"]))
            mapping[source_rel] = (relative.parent / "_index.md").as_posix() if source_rel in config.get("indexes", []) else relative.as_posix()
        examples, example_dirs, example_descriptions = linked_examples(
            source_files, repo, repo=repo, sha=dev_sha, working=True, known_paths=known_paths,
        )
        mapping.update({
            path: example_content_path(path)
            for path in examples
        })
        if examples or example_dirs:
            mapping["examples"] = "examples/_index.md"
            mapping["examples/README.md"] = "examples/_index.md"
            mapping.update({path: "examples/_index.md" for path in example_dirs})
        edit_branch = branch
        if not edit_branch:
            result = subprocess.run(["git", "-C", str(repo), "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            edit_branch = result.stdout.strip().removeprefix("origin/") if result.returncode == 0 else ""
        for source_file in source_files:
            source_rel = source_file.relative_to(repo).as_posix()
            if source_file.suffix.lower() != ".md":
                continue
            output_path = mapping[source_rel]
            destination = DOCS_OUT / product / version / output_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            original = source_file.read_text(encoding="utf-8")
            page_body = adapt_page_markdown(
                original, product=product, version=version, config=config, repo=repo, sha=dev_sha,
                title=title_for(source_file, original), source_path=source_rel, selected=mapping,
                assets=STATIC_OUT, working=True, known_paths=known_paths,
            )
            edit_url = f"{config['repo']}/edit/{edit_branch}/{source_rel}" if edit_branch else None
            source_mount = re.escape(f".cache/docs/{product}/dev/")
            path_base = (
                {"from": "^" + source_mount + re.escape(output_path) + "$", "to": source_rel}
                if source_rel in config.get("indexes", []) else
                {"from": "^" + source_mount, "to": config["content_root"] + "/"}
            )
            content_metadata = page_metadata(product, source_rel, original, navigation)
            metadata = {
                "title": title_for(source_file, original), "product": product, "version": version,
                "version_label": dev_label, "source_commit": dev_sha, "source_repo": config["repo"],
                "source_path": source_rel, "issue_url": config["issues"], "version_archive": False,
                "github_repo": config["repo"], "github_branch": dev_sha,
                "github_project_repo": config["repo"],
                "github_subdir": "",
                "path_base_for_github_subdir": path_base,
                "description": content_metadata["summary"],
                **content_metadata,
                "preview_dirty": bool(source_status), "edit_url": edit_url,
                "cascade": {
                    "product": product, "version": version, "version_label": dev_label,
                    "source_commit": dev_sha, "version_archive": False,
                    "preview_dirty": bool(source_status),
                },
            }
            shortcode = "{{< docs-version >}}\n\n{{< docs-mobile-toc >}}\n\n"
            destination.write_text(
                frontmatter(metadata) + shortcode + page_body
                + "\n\n{{< docs-source-links >}}\n\n{{< docs-related >}}\n",
                encoding="utf-8",
            )
            source_map.append({"product": product, "version": version, "source_path": source_rel,
                               "content_path": output_path, "source_commit": dev_sha,
                               "url": site_url(product, version, output_path), "dirty": bool(source_status)})
        source_map.extend(write_example_pages(
            product, version, dev_label, dev_sha, config, examples, example_dirs,
            example_descriptions, known_paths, STATIC_OUT, True, source_status, edit_branch,
        ))
        versions.append({"slug": "dev", "label": dev_label, "sha": dev_sha, "default": False})
        products_out[product] = {**config, "versions": versions}
        print(f"{product}: dev {dev_sha[:12]}" + (" (dirty preview)" if source_status else ""))

    (DATA_OUT / "docs_build_versions.json").write_text(
        json.dumps({"products": products_out}, indent=2) + "\n", encoding="utf-8"
    )
    (DATA_OUT / "docs_sources.json").write_text(json.dumps(source_map, indent=2) + "\n", encoding="utf-8")


def update_docs(product: str, ref: str) -> None:
    products = catalog()["products"]
    if product not in products:
        raise RuntimeError(f"unknown product {product!r}; choose one of: {', '.join(products)}")
    if not GIT_REF.fullmatch(ref) and not GIT_SHA.fullmatch(ref):
        raise RuntimeError("REF must be a Git branch, tag, or full commit SHA")
    if ".." in ref or "//" in ref or "@{" in ref or ref.endswith(("/", ".", ".lock")):
        raise RuntimeError("REF is not a valid Git branch, tag, or full commit SHA")
    repo = SOURCES / product
    if git(repo, "status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError(f"{product} source checkout is dirty; preserve or commit the changes before updating")
    run(["git", "-C", str(repo), "fetch", "origin", ref])
    commit = git(repo, "rev-parse", "FETCH_HEAD^{commit}")
    run(["git", "-C", str(repo), "checkout", "--detach", commit])
    print(f"Checked out {product} at {commit}. Review the website pointer; it was not staged or committed.")


def add_docs_version(product: str, ref: str) -> None:
    data = catalog()
    products = data["products"]
    if product not in products:
        raise RuntimeError(f"unknown product {product!r}; choose one of: {', '.join(products)}")
    if not RELEASE_TAG.fullmatch(ref):
        raise RuntimeError("REF must be a full release tag such as v1.2.3")
    config = products[product]
    if any(release["version"] == ref or release["tag"] == ref for release in config["releases"]):
        raise RuntimeError(f"{product} already has a catalog entry for {ref}")
    repo = SOURCES / product
    run(["git", "-C", str(repo), "fetch", "--depth=1", "origin", f"refs/tags/{ref}:refs/tags/{ref}"])
    sha = git(repo, "rev-parse", f"{ref}^{{commit}}")
    for required in config["required"]:
        result = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}:{required}"])
        if result.returncode:
            raise RuntimeError(f"{product} {ref} is missing required docs path {required}")
    config["releases"].append({"version": ref, "label": ref, "tag": ref, "sha": sha, "default": False})
    config["releases"].sort(key=lambda entry: tuple(int(n) for n in re.findall(r"\d+", entry["version"])), reverse=True)
    CATALOG.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Added {product} {ref} at {sha}; review data/docs_versions.json and promote its default explicitly if desired.")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    commands.add_parser("check-adapter")
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--mode", choices=("build", "serve"), required=True)
    for name in ("update-docs", "add-docs-version"):
        command = commands.add_parser(name)
        command.add_argument("--product", required=True)
        command.add_argument("--ref", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            init()
        elif args.command == "check-adapter":
            check_adapter()
            print("Documentation adapter checks passed.")
        elif args.command == "prepare":
            prepare(args.mode)
        elif args.command == "update-docs":
            update_docs(args.product, args.ref)
        elif args.command == "add-docs-version":
            add_docs_version(args.product, args.ref)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"docs: {error}\n")


if __name__ == "__main__":
    main()
