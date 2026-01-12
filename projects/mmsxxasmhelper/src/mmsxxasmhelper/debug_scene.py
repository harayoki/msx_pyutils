"""
SCREEN0 デバッグ画面用ユーティリティ。
"""

from __future__ import annotations

from typing import Sequence

from mmsxxasmhelper.core import (
    ADD,
    BIT,
    CALL,
    CP,
    EX,
    HALT,
    INC,
    JP,
    JP_mHL,
    JR_C,
    LD,
    RET,
    RET_NZ,
    XOR,
    Block,
    Func,
)
from mmsxxasmhelper.msxutils import (
    INITXT,
    INPUT_KEY_BIT,
    replace_screen0_yen_with_slash_macro,
    set_screen_colors_macro,
    write_text_with_cursor_macro,
)
from mmsxxasmhelper.utils import DEFAULT_FUNC_GROUP_NAME, unique_label

__all__ = ["build_screen0_debug_scene"]


def build_screen0_debug_scene(
    pages: Sequence[Sequence[str]],
    *,
    update_input_func: Func,
    update_input_addr: int | None = None,
    input_hold_addr: int | None = None,
    input_trg_addr: int,
    page_index_addr: int | None = None,
    group: str = DEFAULT_FUNC_GROUP_NAME,
    title_lines: Sequence[str] | None = None,
    title_row: int = 0,
    title_centered: bool = True,
    header_lines: Sequence[str] | None = None,
    header_row: int | None = None,
    header_col: int = 2,
    top_row: int = 4,
    label_col: int = 2,
    screen0_name_base: int = 0x0000,
    render_hook_func: Func | None = None,
) -> tuple[Func, Sequence[Func]]:
    """SCREEN0 デバッグ画面を生成する。"""

    if not pages:
        raise ValueError("pages が空です")

    title_lines = title_lines or ["", "DEBUG INFO", ""]
    title_height = len(title_lines)
    if header_row is None:
        header_row = title_row + title_height

    header_height = len(header_lines or [])
    if header_height:
        header_bottom_row = header_row + header_height - 1
        if top_row <= header_bottom_row:
            top_row = header_bottom_row + 2
    elif title_height:
        title_bottom_row = title_row + title_height - 1
        if top_row <= title_bottom_row:
            top_row = title_bottom_row + 2

    for page in pages:
        if top_row + len(page) > 24:
            raise ValueError("表示行が SCREEN 0 の 24 行を超えています。")

    page_prefix = unique_label("DEBUG_PAGE")
    page_funcs: list[Func] = []

    def emit_title_and_header(block: Block) -> None:
        if title_lines:
            for idx, line in enumerate(title_lines):
                if not line:
                    continue
                if title_centered:
                    col = max((40 - len(line)) // 2, 0)
                else:
                    col = header_col
                write_text_with_cursor_macro(
                    block, line, col, title_row + idx, name_table=screen0_name_base
                )

        for idx, line in enumerate(header_lines or []):
            write_text_with_cursor_macro(
                block,
                line,
                header_col,
                header_row + idx,
                name_table=screen0_name_base,
            )

    for page_index, page_lines in enumerate(pages):

        def render_page(block: Block, lines: Sequence[str] = page_lines) -> None:
            CALL(block, INITXT)
            set_screen_colors_macro(block, 15, 0, 0, current_screen_mode=0)
            replace_screen0_yen_with_slash_macro(block)
            emit_title_and_header(block)
            for idx, line in enumerate(lines):
                write_text_with_cursor_macro(
                    block,
                    line,
                    label_col,
                    top_row + idx,
                    name_table=screen0_name_base,
                )
            RET(block)

        page_funcs.append(
            Func(
                f"{page_prefix}_{page_index}",
                render_page,
                group=group,
            )
        )

    DRAW_PAGE_JT_LABEL = unique_label("__DEBUG_PAGE_JT__")

    def draw_page_dispatch(block: Block) -> None:
        LD.L_A(block)
        LD.H_n8(block, 0)
        ADD.HL_HL(block)
        LD.DE_label(block, DRAW_PAGE_JT_LABEL)
        ADD.HL_DE(block)
        LD.E_mHL(block)
        INC.HL(block)
        LD.D_mHL(block)
        EX.DE_HL(block)
        JP_mHL(block)

    DRAW_PAGE_DISPATCH = Func(
        "DEBUG_PAGE_DISPATCH",
        draw_page_dispatch,
        group=group,
    )

    def emit_page_tables(block: Block) -> None:
        block.label(DRAW_PAGE_JT_LABEL)
        for func in page_funcs:
            pos = block.emit(0, 0)
            block.add_abs16_fixup(pos, func.name)

    PAGE_TABLE_FUNC = Func(
        "DEBUG_PAGE_TABLES",
        emit_page_tables,
        no_auto_ret=True,
        group=group,
    )

    def debug_scene(block: Block) -> None:
        if page_index_addr is None:
            XOR.A(block)
        else:
            LD.A_mn16(block, page_index_addr)
            CP.n8(block, len(page_funcs))
            LABEL_PAGE_OK = unique_label("__DEBUG_PAGE_OK__")
            JR_C(block, LABEL_PAGE_OK)
            XOR.A(block)
            block.label(LABEL_PAGE_OK)

        DRAW_PAGE_DISPATCH.call(block)
        if render_hook_func is not None:
            render_hook_func.call(block)

        if input_hold_addr is not None:
            LABEL_WAIT_RELEASE = unique_label("__DEBUG_WAIT_RELEASE__")
            block.label(LABEL_WAIT_RELEASE)
            HALT(block)
            if update_input_addr is None:
                update_input_func.call(block)
            else:
                CALL(block, update_input_addr)
            LD.A_mn16(block, input_hold_addr)
            BIT.n8_A(block, INPUT_KEY_BIT.L_ESC)
            JR_NZ(block, LABEL_WAIT_RELEASE)

        LABEL_DEBUG_LOOP = unique_label("__DEBUG_LOOP__")
        block.label(LABEL_DEBUG_LOOP)
        HALT(block)
        if update_input_addr is None:
            update_input_func.call(block)
        else:
            CALL(block, update_input_addr)

        LD.A_mn16(block, input_trg_addr)
        BIT.n8_A(block, INPUT_KEY_BIT.L_ESC)
        RET_NZ(block)

        JP(block, LABEL_DEBUG_LOOP)

    return Func("DEBUG_SCENE", debug_scene, group=group), [PAGE_TABLE_FUNC]
