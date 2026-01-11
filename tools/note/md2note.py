import argparse
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlparse


LINK_PATTERN = re.compile(r"(!?\[[^\]]*\]\()([^)]+)(\))")


def _split_target(target: str) -> tuple[str, str]:
    stripped = target.strip()
    if not stripped:
        return "", ""
    parts = stripped.split(maxsplit=1)
    url = parts[0]
    suffix = f" {parts[1]}" if len(parts) > 1 else ""
    return url, suffix


def _build_absolute_url(
    url: str,
    md_path: Path,
    docs_root: Path,
    github_pages_root: str,
) -> str:
    if not url or url.startswith("#"):
        return url
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return url
    root = github_pages_root.rstrip("/") + "/"
    path = parsed.path
    if path.startswith("/"):
        rel_path = Path(path.lstrip("/"))
    else:
        resolved = (md_path.parent / path).resolve()
        try:
            rel_path = resolved.relative_to(docs_root.resolve())
        except ValueError:
            try:
                rel_path = resolved.relative_to(md_path.parent.resolve())
            except ValueError:
                rel_path = Path(path)
    encoded_path = quote(rel_path.as_posix())
    absolute = f"{root}{encoded_path}"
    if parsed.query:
        absolute = f"{absolute}?{parsed.query}"
    if parsed.fragment:
        absolute = f"{absolute}#{parsed.fragment}"
    return absolute


def convert_markdown(content: str, md_path: Path, docs_root: Path, github_pages_root: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        prefix, target, suffix = match.groups()
        url, extra = _split_target(target)
        new_url = _build_absolute_url(url, md_path, docs_root, github_pages_root)
        return f"{prefix}{new_url}{extra}{suffix}"

    return LINK_PATTERN.sub(replacer, content)


def main():
    parser = argparse.ArgumentParser(description="Convert markdown notes to Note format.")
    parser.add_argument(
        "md_path",
        type=Path,
        help="Path to the input markdown file.",
    )
    parser.add_argument(
        "--github-pages-root",
        type=str,
        default="https://harayoki.github.io/msx_pyutils/",
        help="Root URL for GitHub Pages.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default="docs/notes/",
        help="Directory to save the converted Note files.",
    )
    args = parser.parse_args()

    md_path: Path = args.md_path
    github_pages_root: str = args.github_pages_root
    output_dir: Path = args.output_dir
    docs_root = output_dir.resolve().parent

    content = md_path.read_text(encoding="utf-8")
    converted = convert_markdown(content, md_path, docs_root, github_pages_root)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / md_path.name
    output_path.write_text(converted, encoding="utf-8")


if __name__ == "__main__":
    main()


