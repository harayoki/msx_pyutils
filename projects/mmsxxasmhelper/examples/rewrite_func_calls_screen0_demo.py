"""Self-modifying CALL demo for ``rewrite_func_calls``.

CALL 先を書き換えた後に画面表示が変わることを確認する
SCREEN 0 用の ROM サンプル。
``dist/rewrite_func_calls_screen0.rom`` に出力する。
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from mmsxxasmhelper.core import (
    CALL,
    CALL_label,
    DB,
    Block,
    Func,
    INC,
    JR,
    JR_Z,
    LD,
    LDIR,
    OR,
    JP_mHL,
    NOP,
    dynamic_label_change,
)
from mmsxxasmhelper.msxutils import (
    BAKCLR,
    BDRCLR,
    CHGCLR,
    CHPUT,
    FORCLR,
    INITXT,
    place_msx_rom_header_macro,
    store_stack_pointer_macro,
)
from mmsxxasmhelper.utils import pad_bytes, debug_print_labels, print_bytes


CHGET = 0x009F
PAGE_SIZE = 0x4000
ORIGIN = 0x4000
RAM_ORIGIN = 0xC000


def build_rewrite_func_calls_rom() -> bytes:
    """組み立てた ROM バイト列を返す。"""

    payload = Block()
    payload.label("payload_entry")

    def print_string(block: Block) -> None:
        """HL を先頭にした 0x00 終端文字列を CHPUT で表示。"""
        block.label("print_string_loop")
        LD.A_mHL(payload)
        OR.A(block)  # ZF=1 なら終端
        JR_Z(block, "print_string_end")
        CALL(block, CHPUT)
        INC.HL(block)
        JR(block, "print_string_loop")
        block.label("print_string_end")
    PRINT_STRING = Func("print_string", print_string, group="payload")

    def message_before(block: Block) -> None:
        LD.HL_label(block, "MESSAGE_BEFORE")
        PRINT_STRING.call(block)
    PRINT_MESSAGE1= Func("PRINT_MESSAGE1", message_before, group="payload")

    def message_after(block: Block) -> None:
        LD.HL_label(block, "MESSAGE_AFTER")
        PRINT_STRING.call(block)
    PRINT_MESSAGE2 = Func("PRINT_MESSAGE2", message_after, group="payload")

    def message_proxy(block: Block) -> None:
        """CALL 先を書き換えるためのダミー関数。"""
        pass
    PRINT_MESSAGE_PROXY = Func("PRINT_MESSAGE_PROXY", message_proxy, group="payload")

    JR(payload, "main_body")

    PRINT_STRING.define(payload)
    PRINT_MESSAGE1.define(payload)
    PRINT_MESSAGE2.define(payload)
    NOP(payload)
    NOP(payload)
    PRINT_MESSAGE_PROXY.define(payload)
    NOP(payload)
    NOP(payload)

    payload.label("main_body")

    CALL(payload, INITXT)
    LD.A_n8(payload, 0x0F)  # 白
    LD.mn16_A(payload, FORCLR)
    LD.A_n8(payload, 0x04)  # 青
    LD.mn16_A(payload, BAKCLR)
    LD.mn16_A(payload, BDRCLR)
    CALL(payload, CHGCLR)

    LD.HL_label(payload, "HEADER_TEXT")
    PRINT_STRING.call(payload)

    payload.label("LOOOOOP")  # -------------------- LOOP --------------------

    dynamic_label_change(payload, PRINT_MESSAGE_PROXY, PRINT_MESSAGE1, debuglog=True)
    PRINT_MESSAGE_PROXY.call(payload)

    LD.HL_label(payload, "PROMPT_TEXT")
    PRINT_STRING.call(payload)
    CALL(payload, CHGET)

    dynamic_label_change(payload, PRINT_MESSAGE_PROXY, PRINT_MESSAGE2, debuglog=True)
    PRINT_MESSAGE_PROXY.call(payload)

    LD.HL_label(payload, "PROMPT_TEXT")
    PRINT_STRING.call(payload)
    CALL(payload, CHGET)

    JR(payload, "LOOOOOP")  # -------------------- LOOP --------------------

    payload.label("HEADER_TEXT")
    DB(payload, *"rewrite_func_calls demo\r\n\r\n".encode("ascii"), 0x00)

    payload.label("PROMPT_TEXT")
    DB(payload, *"Press any key to toggle...\r\n".encode("ascii"), 0x00)

    payload.label("MESSAGE_BEFORE")
    DB(payload, *"MESSAGE: BEFORE\r\n".encode("ascii"), 0x00)

    payload.label("MESSAGE_AFTER")
    DB(payload, *"MESSAGE: AFTER\r\n".encode("ascii"), 0x00)

    payload_bytes = payload.finalize(origin=RAM_ORIGIN, groups=["payload"])
    debug_print_labels(payload)

    b = Block()
    place_msx_rom_header_macro(b, entry_point=0x4010)

    b.label("main")
    store_stack_pointer_macro(b)

    LD.HL_label(b, "payload_bytes")
    LD.DE_n16(b, RAM_ORIGIN)
    LD.BC_n16(b, len(payload_bytes))
    LDIR(b)
    LD.HL_n16(b, RAM_ORIGIN)
    JP_mHL(b)

    b.label("payload_bytes")
    DB(b, *payload_bytes)

    rom = b.finalize(origin=ORIGIN, groups=["rom"])
    print_bytes(rom)
    debug_print_labels(b)
    return bytes(pad_bytes(list(rom), PAGE_SIZE, 0x00))


def main() -> None:
    rom = build_rewrite_func_calls_rom()
    dist_dir = Path(__file__).resolve().parent / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    out_path = dist_dir / "rewrite_func_calls_screen0.rom"
    out_path.write_bytes(rom)
    print(f"Wrote {len(rom)} bytes to {out_path}")


if __name__ == "__main__":
    main()
