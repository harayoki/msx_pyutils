from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, List, Sequence

import gradio as gr


AUTO_ADVANCE_INTERVAL_KEYS = ["NONE", "3min", "1min", "30s", "10s", "5s", "3s", "1s", "MAX"]
AUTO_SCROLL_LEVEL_CHOICES = ["NONE", "1", "2", "3", "4", "5", "6", "7", "8", "MAX"]
AUTO_PAGE_EDGE_CHOICES = ["NO", "YES"]
VDP_WAIT_CHOICES = ["WAIT", "NOWAIT"]
START_AT_CHOICES = ["top", "bottom"]
MERGE_MODE_CHOICES = [
    "すべて別画像",
    "すべて縦結合",
    "連番のみ縦結合",
]


@dataclass(frozen=True)
class SequenceRun:
    paths: List[Path]
    first_index: int


def _flatten_files(files: Iterable[object]) -> List[Path]:
    resolved: List[Path] = []
    for item in files:
        if isinstance(item, Path):
            resolved.append(item)
            continue
        if isinstance(item, str):
            resolved.append(Path(item))
            continue
        if isinstance(item, dict) and "name" in item:
            resolved.append(Path(item["name"]))
            continue
        name = getattr(item, "name", None)
        if name:
            resolved.append(Path(name))
    return resolved


def _resolve_file_path(item: object | None) -> Path | None:
    if item is None:
        return None
    if isinstance(item, Path):
        return item
    if isinstance(item, str):
        return Path(item)
    if isinstance(item, dict) and "name" in item:
        return Path(item["name"])
    name = getattr(item, "name", None)
    if name:
        return Path(name)
    return None


def _group_by_sequence(paths: Sequence[Path]) -> List[List[Path]]:
    pattern = re.compile(r"^(.*?)(\d+)(\.[^.]+)$")
    indexed = {path: index for index, path in enumerate(paths)}
    singletons: List[SequenceRun] = []
    grouped: dict[tuple[str, str, int], List[tuple[int, Path]]] = {}

    for path in paths:
        match = pattern.match(path.name)
        if not match:
            singletons.append(SequenceRun(paths=[path], first_index=indexed[path]))
            continue
        prefix, number, suffix = match.groups()
        key = (prefix, suffix, len(number))
        grouped.setdefault(key, []).append((int(number), path))

    runs: List[SequenceRun] = []
    for items in grouped.values():
        items.sort(key=lambda item: item[0])
        current: List[Path] = [items[0][1]]
        for (prev_num, _), (num, path) in zip(items, items[1:]):
            if num == prev_num + 1:
                current.append(path)
            else:
                runs.append(
                    SequenceRun(
                        paths=current,
                        first_index=min(indexed[p] for p in current),
                    )
                )
                current = [path]
        runs.append(
            SequenceRun(
                paths=current,
                first_index=min(indexed[p] for p in current),
            )
        )

    grouped_runs: List[SequenceRun] = []
    for run in runs:
        if len(run.paths) >= 2:
            grouped_runs.append(
                SequenceRun(paths=run.paths, first_index=run.first_index)
            )
        else:
            singletons.append(run)

    combined = grouped_runs + singletons
    combined.sort(key=lambda run: run.first_index)
    return [run.paths for run in combined]


def _build_image_groups(files: Sequence[Path], merge_mode: str) -> List[List[Path]]:
    sorted_files = sorted(files, key=lambda path: path.name)
    if merge_mode == "すべて縦結合":
        return [sorted_files]
    if merge_mode == "連番のみ縦結合":
        return _group_by_sequence(sorted_files)
    return [[path] for path in sorted_files]


def _parse_start_at_override(value: str) -> List[str]:
    if not value.strip():
        return []
    entries = [entry.strip() for entry in value.split(",") if entry.strip()]
    for entry in entries:
        if entry not in START_AT_CHOICES:
            raise ValueError(
                "start-at-override は top または bottom をカンマ区切りで指定してください。"
            )
    return entries


def _format_command(cmd: Sequence[str]) -> str:
    return " ".join(cmd)


def build_rom(
    files: List[object],
    merge_mode: str,
    exe_path: str,
    msx1pq_cli_path: str,
    output_name: str,
    background: str,
    msx1pq_cli_distance: float | None,
    msx1pq_cli_no_dither: bool,
    no_cache: bool,
    fill_byte: int,
    title_wait_seconds: int,
    skip_title_screen: bool,
    rom_info: bool,
    rom_type_suffix: bool,
    beep: bool,
    bgm: bool,
    bgm_path: object | None,
    bgm_fps: int,
    auto_page: str,
    auto_page_edge: str,
    auto_scroll: str,
    start_at: str,
    start_at_override: str,
    start_at_random: bool,
    debug_build: bool,
    vdp_wait_for_name_table: str,
    vdp_wait_for_pattern_gen: str,
    vdp_wait_for_color_table: str,
) -> tuple[str, str | None]:
    if not files:
        raise gr.Error("PNG を1枚以上アップロードしてください。")

    file_paths = _flatten_files(files)
    if not file_paths:
        raise gr.Error("PNG を1枚以上アップロードしてください。")
    image_groups = _build_image_groups(file_paths, merge_mode)
    if not image_groups:
        raise gr.Error("入力画像のグループ化に失敗しました。")

    exe = exe_path.strip() or "scroll_sc2_viewer_megarom"
    output_name = output_name.strip() or "scroll_sc2_viewer.rom"

    bgm_file_path = _resolve_file_path(bgm_path)
    if bgm and not bgm_file_path:
        raise gr.Error("BGM を有効にする場合は BGM ファイルを指定してください。")

    overrides = _parse_start_at_override(start_at_override)

    with TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_path = temp_dir_path / output_name
        work_dir = temp_dir_path / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        cmd = [exe]
        for group in image_groups:
            cmd.append("-i")
            cmd.extend(str(path) for path in group)
        cmd.extend(["-o", str(output_path)])
        cmd.extend(["-bg", background])
        cmd.extend(["-W", str(work_dir)])
        cmd.extend(["-F", str(int(fill_byte))])
        cmd.extend(["--title-wait-seconds", str(int(title_wait_seconds))])
        cmd.extend(["--auto-page", auto_page])
        cmd.extend(["--auto-page-edge", auto_page_edge])
        cmd.extend(["--auto-scroll", auto_scroll])
        cmd.extend(["--start-at", start_at])
        cmd.extend(["-vwn", vdp_wait_for_name_table])
        cmd.extend(["-vwp", vdp_wait_for_pattern_gen])
        cmd.extend(["-vwc", vdp_wait_for_color_table])

        if overrides:
            cmd.append("--start-at-override")
            cmd.extend(overrides)

        if msx1pq_cli_path.strip():
            cmd.extend(["--msx1pq-cli", msx1pq_cli_path.strip()])
        if msx1pq_cli_distance is not None:
            cmd.extend(["--msx1pq-cli-distance", str(msx1pq_cli_distance)])
        if msx1pq_cli_no_dither:
            cmd.append("--msx1pq-cli-no-dither")
        if no_cache:
            cmd.append("--no-cache")
        if skip_title_screen:
            cmd.append("--skip-title-screen")
        if not rom_info:
            cmd.append("--no-rom-info")
        if not rom_type_suffix:
            cmd.append("--no-rom-type-suffix")
        if beep:
            cmd.append("--beep")
        if bgm:
            cmd.append("--bgm")
            cmd.extend(["--bgm-path", str(bgm_file_path)])
            cmd.extend(["--bgm-fps", str(bgm_fps)])
        if start_at_random:
            cmd.append("--start-at-random")
        if debug_build:
            cmd.append("--debug-build")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            message = (
                "ROM 生成に失敗しました。\n\n"
                f"command:\n{_format_command(cmd)}\n\n"
                f"stdout:\n{stdout}\n\n"
                f"stderr:\n{stderr}"
            )
            raise gr.Error(message) from exc

        if not output_path.exists():
            raise gr.Error("ROM が生成されませんでした。")

        log_text = (
            "ROM を生成しました。\n\n"
            f"command:\n{_format_command(cmd)}\n\n"
            f"stdout:\n{result.stdout}\n\n"
            f"stderr:\n{result.stderr}"
        )
        return log_text, str(output_path)


def _build_interface() -> gr.Blocks:
    with gr.Blocks(title="SC2 Viewer MegaROM Builder") as demo:
        gr.Markdown(
            """
# SC2 Viewer MegaROM Builder

`make_scroll_sc2_viewer_megarom_exe.py` で作成した実行ファイルと `msx1pq_cli` を使って
SCREEN2 縦スクロール MegaROM を生成します。画像をアップロードして **ROM を生成** を押すと
ROM をダウンロードできます。
"""
        )
        with gr.Row():
            files = gr.File(
                label="入力 PNG (複数可)",
                file_count="multiple",
                file_types=[".png"],
            )
            merge_mode = gr.Radio(
                choices=MERGE_MODE_CHOICES,
                value=MERGE_MODE_CHOICES[0],
                label="画像の結合ルール",
            )
        with gr.Row():
            exe_path = gr.Textbox(
                label="scroll_sc2_viewer_megarom 実行ファイルのパス",
                value="scroll_sc2_viewer_megarom",
            )
            msx1pq_cli_path = gr.Textbox(
                label="msx1pq_cli 実行ファイルのパス (任意)",
                value="",
            )
        output_name = gr.Textbox(
            label="出力 ROM 名",
            value="scroll_sc2_viewer.rom",
        )
        background = gr.Textbox(
            label="背景色 (16進カラー)",
            value="#000000",
        )

        with gr.Accordion("量子化設定 (msx1pq_cli)", open=False):
            msx1pq_cli_distance = gr.Number(
                label="msx1pq_cli distance",
                value=None,
            )
            msx1pq_cli_no_dither = gr.Checkbox(
                label="msx1pq_cli --no-dither",
                value=False,
            )
            no_cache = gr.Checkbox(
                label="量子化キャッシュを無効化 (--no-cache)",
                value=False,
            )

        with gr.Accordion("ROM オプション", open=False):
            with gr.Row():
                fill_byte = gr.Number(
                    label="空き領域の埋めバイト (-F)",
                    value=0xFF,
                    precision=0,
                )
                title_wait_seconds = gr.Number(
                    label="タイトル待ち秒数 (--title-wait-seconds)",
                    value=3,
                    precision=0,
                )
                skip_title_screen = gr.Checkbox(
                    label="タイトル画面をスキップ (--skip-title-screen)",
                    value=False,
                )
            with gr.Row():
                rom_info = gr.Checkbox(
                    label="ROM 情報を埋め込む (--rom-info)",
                    value=True,
                )
                rom_type_suffix = gr.Checkbox(
                    label="ROM タイプのサフィックス追加 (--rom-type-suffix)",
                    value=True,
                )
                beep = gr.Checkbox(
                    label="BEEP を有効 (--beep)",
                    value=False,
                )
            with gr.Row():
                bgm = gr.Checkbox(
                    label="BGM を有効 (--bgm)",
                    value=False,
                )
                bgm_path = gr.File(
                    label="BGM ファイル (--bgm-path)",
                    file_count="single",
                )
                bgm_fps = gr.Dropdown(
                    label="BGM FPS (--bgm-fps)",
                    choices=[30, 60],
                    value=30,
                )

        with gr.Accordion("自動スクロール/ページ送り", open=False):
            with gr.Row():
                auto_page = gr.Dropdown(
                    label="自動ページ送り (--auto-page)",
                    choices=AUTO_ADVANCE_INTERVAL_KEYS,
                    value="10s",
                )
                auto_page_edge = gr.Dropdown(
                    label="端での自動ページ送り (--auto-page-edge)",
                    choices=AUTO_PAGE_EDGE_CHOICES,
                    value="YES",
                )
                auto_scroll = gr.Dropdown(
                    label="自動スクロール (--auto-scroll)",
                    choices=AUTO_SCROLL_LEVEL_CHOICES,
                    value="6",
                )

        with gr.Accordion("開始位置とスクロール設定", open=False):
            with gr.Row():
                start_at = gr.Dropdown(
                    label="開始位置 (--start-at)",
                    choices=START_AT_CHOICES,
                    value="top",
                )
                start_at_override = gr.Textbox(
                    label="開始位置の上書きリスト (--start-at-override)",
                    placeholder="top,bottom,top",
                )
                start_at_random = gr.Checkbox(
                    label="開始位置をランダムに (--start-at-random)",
                    value=False,
                )

        with gr.Accordion("VDP Wait 設定", open=False):
            with gr.Row():
                vdp_wait_for_name_table = gr.Dropdown(
                    label="ネームテーブル転送待機 (-vwn)",
                    choices=VDP_WAIT_CHOICES,
                    value="NOWAIT",
                )
                vdp_wait_for_pattern_gen = gr.Dropdown(
                    label="パターン転送待機 (-vwp)",
                    choices=VDP_WAIT_CHOICES,
                    value="NOWAIT",
                )
                vdp_wait_for_color_table = gr.Dropdown(
                    label="カラーテーブル転送待機 (-vwc)",
                    choices=VDP_WAIT_CHOICES,
                    value="NOWAIT",
                )

        debug_build = gr.Checkbox(
            label="デバッグビルド (--debug-build)",
            value=False,
        )

        run_button = gr.Button("ROM を生成")
        output_log = gr.Textbox(
            label="ログ",
            lines=12,
        )
        output_file = gr.File(label="生成された ROM")

        run_button.click(
            build_rom,
            inputs=[
                files,
                merge_mode,
                exe_path,
                msx1pq_cli_path,
                output_name,
                background,
                msx1pq_cli_distance,
                msx1pq_cli_no_dither,
                no_cache,
                fill_byte,
                title_wait_seconds,
                skip_title_screen,
                rom_info,
                rom_type_suffix,
                beep,
                bgm,
                bgm_path,
                bgm_fps,
                auto_page,
                auto_page_edge,
                auto_scroll,
                start_at,
                start_at_override,
                start_at_random,
                debug_build,
                vdp_wait_for_name_table,
                vdp_wait_for_pattern_gen,
                vdp_wait_for_color_table,
            ],
            outputs=[output_log, output_file],
        )
    return demo


app = _build_interface()

if __name__ == "__main__":
    app.launch()
