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
    ADD,
    AND,
    CALL,
    CP,
    DB,
    Block,
    Func,
    INC,
    JR,
    JR_C,
    JR_Z,
    LD,
    LDIR,
    OR,
    JP_mHL,
    SRL,
    rewrite_func_calls,
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
from mmsxxasmhelper.utils import pad_bytes, unique_label


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
        LD.rr(block, "A", "mHL")
        OR.A(block)  # ZF=1 なら終端
        JR_Z(block, "print_string_end")
        CALL(block, CHPUT)
        INC.HL(block)
        JR(block, "print_string_loop")
        block.label("print_string_end")

    PRINT_STRING = Func("print_string", print_string, group="payload")

    def print_hex_nibble(block: Block) -> None:
        """A の下位 4bit を 1 桁の 16進で表示。"""

        label_digit = unique_label("print_hex_nibble_digit")
        label_done = unique_label("print_hex_nibble_done")
        CP.n8(block, 10)
        JR_C(block, label_digit)
        ADD.A_n8(block, 0x37)
        JR(block, label_done)
        block.label(label_digit)
        ADD.A_n8(block, 0x30)
        block.label(label_done)
        CALL(block, CHPUT)

    def print_hex_byte(block: Block) -> None:
        """A の値を 2 桁の 16進で表示。"""

        LD.B_A(block)
        LD.A_B(block)
        SRL.A(block)
        SRL.A(block)
        SRL.A(block)
        SRL.A(block)
        print_hex_nibble(block)
        LD.A_B(block)
        AND.n8(block, 0x0F)
        print_hex_nibble(block)

    def print_hex_word(block: Block) -> None:
        """DE の値を 4 桁の 16進で表示。"""

        LD.rr(block, "A", "D")
        print_hex_byte(block)
        LD.rr(block, "A", "E")
        print_hex_byte(block)

    PRINT_HEX_WORD = Func("print_hex_word", print_hex_word, group="payload")

    def message_before(block: Block) -> None:
        LD.HL_label(block, "MESSAGE_BEFORE")
        PRINT_STRING.call(block)

    def message_after(block: Block) -> None:
        LD.HL_label(block, "MESSAGE_AFTER")
        PRINT_STRING.call(block)

    PRINT_MESSAGE = Func("print_message", message_before, group="payload")
    PRINT_MESSAGE_ALT = Func("print_message_alt", message_after, group="payload")

    JR(payload, "main_body")

    PRINT_STRING.define(payload)
    PRINT_HEX_WORD.define(payload)
    PRINT_MESSAGE.define(payload)
    PRINT_MESSAGE_ALT.define(payload)

    payload.label("main_body")

    CALL(payload, INITXT)
    LD.A_n8(payload, 0x0F)  # 白
    LD.mn16_A(payload, FORCLR)
    LD.A_n8(payload, 0x01)  # 青
    LD.mn16_A(payload, BAKCLR)
    LD.mn16_A(payload, BDRCLR)
    CALL(payload, CHGCLR)

    LD.HL_label(payload, "HEADER_TEXT")
    PRINT_STRING.call(payload)
    PRINT_MESSAGE.call(payload)

    payload.label("toggle_loop")

    LD.HL_label(payload, "PROMPT_TEXT")
    PRINT_STRING.call(payload)
    CALL(payload, CHGET)

    LD.HL_label(payload, "TOGGLE_FLAG")
    LD.rr(payload, "A", "mHL")
    OR.A(payload)
    JR_Z(payload, "toggle_to_after")

    LD.A_n8(payload, 0x00)
    LD.mHL_A(payload)
    rewrite_func_calls(payload, PRINT_MESSAGE, PRINT_MESSAGE, origin=RAM_ORIGIN, offset=RAM_ORIGIN)
    JR(payload, "toggle_done")

    payload.label("toggle_to_after")
    LD.A_n8(payload, 0x01)
    LD.mHL_A(payload)
    rewrite_func_calls(payload, PRINT_MESSAGE, PRINT_MESSAGE_ALT, origin=RAM_ORIGIN, offset=RAM_ORIGIN)

    payload.label("toggle_done")
    LD.HL_label(payload, "AFTER_LABEL")
    PRINT_STRING.call(payload)
    payload.label("PRINT_MESSAGE_CALL_SITE")
    PRINT_MESSAGE.call(payload)
    LD.HL_label(payload, "ADDR_LABEL")
    PRINT_STRING.call(payload)
    LD.HL_label(payload, "PRINT_MESSAGE_CALL_SITE")
    INC.HL(payload)
    LD.E_mHL(payload)
    INC.HL(payload)
    LD.D_mHL(payload)
    PRINT_HEX_WORD.call(payload)
    LD.HL_label(payload, "NEWLINE")
    PRINT_STRING.call(payload)
    JR(payload, "toggle_loop")

    payload.label("HEADER_TEXT")
    DB(payload, *"rewrite_func_calls demo\r\n\r\n".encode("ascii"), 0x00)

    payload.label("MESSAGE_BEFORE")
    DB(payload, *"MESSAGE: BEFORE\r\n".encode("ascii"), 0x00)

    payload.label("PROMPT_TEXT")
    DB(payload, *"Press any key to toggle...\r\n".encode("ascii"), 0x00)

    payload.label("AFTER_LABEL")
    DB(payload, *"Rewritten call target!\r\n".encode("ascii"), 0x00)

    payload.label("ADDR_LABEL")
    DB(payload, *"CALL TARGET: $".encode("ascii"), 0x00)

    payload.label("NEWLINE")
    DB(payload, *"\r\n".encode("ascii"), 0x00)

    payload.label("MESSAGE_AFTER")
    DB(payload, *"MESSAGE: AFTER\r\n".encode("ascii"), 0x00)

    payload.label("TOGGLE_FLAG")
    DB(payload, 0x00)

    payload_bytes = payload.finalize(origin=RAM_ORIGIN, groups=["payload"])

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
