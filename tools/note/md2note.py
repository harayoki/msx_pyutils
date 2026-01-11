import argparse
from pathlib import Path
from typing import Optional


def main():
    # TODO 実装
    # 引数 mdファイルパス、githubpagesルートURL
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
    pass


if __name__ == "__main__":
    main()


