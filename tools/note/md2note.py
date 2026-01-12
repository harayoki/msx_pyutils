import argparse
import re
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from PIL import Image


MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
IMG_TAG_PATTERN = re.compile(r"<img\s+[^>]*>", re.IGNORECASE)
IMG_ATTR_PATTERN = re.compile(r"(\w+)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)")


def _split_target(target: str) -> tuple[str, str]:
    stripped = target.strip()
    if not stripped:
        return "", ""
    parts = stripped.split(maxsplit=1)
    url = parts[0]
    suffix = f" {parts[1]}" if len(parts) > 1 else ""
    return url, suffix


def _parse_size_value(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    cleaned = value.strip().strip('"').strip("'")
    match = re.match(r"(\d+)", cleaned)
    if not match:
        return None
    return int(match.group(1))


def _parse_style_size(style: Optional[str], key: str) -> Optional[int]:
    if not style:
        return None
    match = re.search(rf"{key}\s*:\s*(\d+)px", style)
    if not match:
        return None
    return int(match.group(1))


def _resolve_local_image(url: str, md_path: Path) -> Optional[Path]:
    if not url or url.startswith("#") or url.startswith("data:"):
        return None
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None
    path_str = unquote(parsed.path)
    if not path_str:
        return None
    if path_str.startswith("/"):
        candidate = (md_path.parent / path_str.lstrip("/")).resolve()
    else:
        candidate = (md_path.parent / path_str).resolve()
    if candidate.exists():
        return candidate
    return None


def _build_suffixed_name(src: Path, width: int, height: int) -> str:
    return f"{src.stem}_{width}x{height}{src.suffix}"


def _copy_image(
    src: Path,
    dest_dir: Path,
    target_size: Optional[tuple[int, int]] = None,
) -> tuple[str, int, int]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if target_size:
        with Image.open(src) as image:
            resized = image.resize(target_size, Image.LANCZOS)
            width, height = resized.size
            dest_path = dest_dir / _build_suffixed_name(src, width, height)
            resized.save(dest_path)
    else:
        with Image.open(src) as image:
            width, height = image.size
        dest_path = dest_dir / _build_suffixed_name(src, width, height)
        shutil.copy2(src, dest_path)
    return dest_path.name, width, height


def _placeholder(name: str, width: int, height: int) -> str:
    return f"[{name}:{width}x{height}]"


def _replace_markdown_images(content: str, md_path: Path, dest_dir: Path) -> str:
    def replacer(match: re.Match[str]) -> str:
        target = match.group(1)
        url, _extra = _split_target(target)
        local_path = _resolve_local_image(url, md_path)
        if not local_path:
            return match.group(0)
        filename, width, height = _copy_image(local_path, dest_dir)
        return _placeholder(filename, width, height)

    return MARKDOWN_IMAGE_PATTERN.sub(replacer, content)


def _replace_html_images(content: str, md_path: Path, dest_dir: Path) -> str:
    def replacer(match: re.Match[str]) -> str:
        tag = match.group(0)
        attrs = {key.lower(): value.strip('"').strip("'") for key, value in IMG_ATTR_PATTERN.findall(tag)}
        src = attrs.get("src", "")
        local_path = _resolve_local_image(src, md_path)
        if not local_path:
            return tag
        width = _parse_size_value(attrs.get("width"))
        height = _parse_size_value(attrs.get("height"))
        style = attrs.get("style")
        width = width or _parse_style_size(style, "width")
        height = height or _parse_style_size(style, "height")
        target_size: Optional[tuple[int, int]] = None
        if width or height:
            with Image.open(local_path) as image:
                orig_width, orig_height = image.size
            if width and height:
                target_size = (width, height)
            elif width:
                target_size = (width, int(orig_height * (width / orig_width)))
            elif height:
                target_size = (int(orig_width * (height / orig_height)), height)
        filename, final_width, final_height = _copy_image(local_path, dest_dir, target_size)
        return _placeholder(filename, final_width, final_height)

    return IMG_TAG_PATTERN.sub(replacer, content)


def main():
    parser = argparse.ArgumentParser(description="Convert markdown notes to Note format.")
    parser.add_argument(
        "md_path",
        type=Path,
        help="Path to the input markdown file.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default="_note_docs/build/",
        help="Directory to save the converted Note files.",
    )
    args = parser.parse_args()

    md_path: Path = args.md_path
    output_dir: Path = args.output_dir

    content = md_path.read_text(encoding="utf-8")
    note_dir = output_dir / md_path.stem
    converted = _replace_html_images(content, md_path, note_dir)
    converted = _replace_markdown_images(converted, md_path, note_dir)

    note_dir.mkdir(parents=True, exist_ok=True)
    output_path = note_dir / f"{md_path.stem}.md.txt"
    print(f"Writing converted note to: {output_path}")
    output_path.write_text(converted, encoding="utf-8")


if __name__ == "__main__":
    main()
