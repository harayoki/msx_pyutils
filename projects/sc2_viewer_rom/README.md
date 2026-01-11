# SC2 Viewer ROM

## スクリプト一覧
- [`sc2_viewer_32k_rom.py`](src/sc2_viewer_32k_rom.py)
  - 32kROMに2枚のSC2画像を表示するROMファイルを作成
- [`sc2_viewer_megarom.py`](src/sc2_viewer_megarom.py)
  - メガロムに約250枚のSC2画像を表示するROMファイルを作成
- [`scroll_sc2_viewer_megarom.py`](src/scroll_sc2_viewer_megarom.py)
  - メガロムに約250枚換算の縦長SC2画像を自動スクロール表示するROMファイルを作成

## 使い方
- 通常は `scroll_sc2_viewer_megarom.py` を使用する。
  - 高度な処理をしているため、動かない場合は `sc2_viewer_megarom.py` を使う。
- メガロムではなく32kROM版が欲しい場合は `sc2_viewer_32k_rom.py` を使う。
- msx1pq_cli に渡す細かいカスタマイズは `--msx1pq-cli-distance` と `--msx1pq-cli-no-dither` のみ提供する。
  - それ以上の調整が必要な場合は msx1pq_cli で量子化済み PNG を作成し、このツールに入力する。

## 動作確認
- それぞれのROMファイルは OPENMSX と webMSX で動作確認済み。
- 実機での動作は未確認。

## BGMファイルについて
- スクロールビューアーでは、VGMファイルを元にした「psgstream」形式の bin をテストで使用している。
  - まだ開発中のため、仕様は今後変更される可能性がある。

---

# SC2 Viewer ROM (English)

## Scripts
- [`sc2_viewer_32k_rom.py`](src/sc2_viewer_32k_rom.py)
  - Creates a ROM for displaying two SC2 images in a 32kROM.
- [`sc2_viewer_megarom.py`](src/sc2_viewer_megarom.py)
  - Creates a MegaROM for displaying around 250 SC2 images.
- [`scroll_sc2_viewer_megarom.py`](src/scroll_sc2_viewer_megarom.py)
  - Creates a MegaROM for auto-scrolling tall SC2 images (equivalent to around 250 images).

## Usage
- Use `scroll_sc2_viewer_megarom.py` by default.
  - If it does not work due to the advanced processing, use `sc2_viewer_megarom.py`.
- If you need a 32kROM version instead of a MegaROM, use `sc2_viewer_32k_rom.py`.
- Only `--msx1pq-cli-distance` and `--msx1pq-cli-no-dither` are exposed for msx1pq_cli customization.
  - For more advanced control, create quantized PNGs with msx1pq_cli directly and feed them into this tool.

## Tested
- The ROMs have been tested on OPENMSX and webMSX.
- Not tested on real hardware.

## BGM files
- The scroll viewer uses a test bin in the experimental "psgstream" format generated from VGM files.
  - Since it is still under development, the specification may change in the future.
