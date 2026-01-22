# MSX PyUtils

[README.md (English version is here)](README.md)

MSX PyUtils は、MSX コンピュータプラットフォーム向けのディスク／ROM 生成や画像変換などを支援する、Python ベースのツールとライブラリのコレクションです。

## Projects

各プロジェクトには使い方をまとめた README があります。

### Python ユーティリティ

* [Basic SC2/SC4 Viewer](projects/basic_sc2_viewer/README.md): SC2/SC4 画像を自動起動の BASIC プログラムで表示できるディスクイメージを生成します（エミュレータ／2DD 実機向け）。
* [MSX Disk](projects/msxdisk/README.md): 指定したファイル／フォルダーから MSX 互換 2DD (720KiB) FAT12 ディスクイメージを作成します。
* [MMSXX ASM Helper](projects/mmsxxasmhelper/README.md): MSX Z80 ニーモニックを Python から呼び出せる WIP ユーティリティライブラリです。
* [SC2 Viewer ROM Tools](projects/sc2_viewer_rom/README.md): SCREEN 2 画像閲覧用の MSX ROM を生成するツール群です（32KiB 切替ビューアーや縦スクロール MegaROM 生成など）。
* [Simple SC2 Converter](projects/simple_sc2_converter/README.md): PNG 画像を MSX Screen 2 (`.sc2`) バイナリやパレット制約 PNG へ変換します（今後の機能更新予定なし）。

## リポジトリ構成

* `docs/`: リポジトリのドキュメント資産。
* `_note_docs/`: 個人用メモや参考資料。
* `_tech_docs/`: 技術メモや設計ドキュメント。
* `projects/`: プロジェクト本体（各フォルダに README あり）。
* `tests/`: テスト用の素材やフィクスチャ。
* `tools/`: 補助スクリプトやユーティリティ。
* `requirements.in` / `requirements.txt`: Python ツール群の依存関係定義。
* `README.md` / `README_ja.md`: トップレベルのドキュメント（英語／日本語）。

## Python 要件

これらのツールは Python 3.11 以降を対象としています。

## 依存関係のインストール（uv）

```
uv pip compile requirements.in -o requirements.txt
uv venv
uv pip sync requirements.txt
source .venv/Scripts/activate
```
