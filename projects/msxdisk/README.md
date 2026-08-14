# MSX Disk / MSXディスクユーティリティ

This package creates 2DD (720KiB) FAT12 disk images for MSX.
The disk image can store specified files and folders together.

* Includes a minimal FAT12 helper to generate disk images that work in MSX format.
* Files and folders to be stored can be specified as arguments. Folders are expanded recursively.
* If there is insufficient space, an error is raised by default. Adding `--allow-partial` will store as much as possible and issue a warning.

---
 
このパッケージは MSX 用の 2DD(720KiB) FAT12 ディスクイメージを作成します。
ディスクイメージには指定したファイルやフォルダーをまとめて格納できます。

* 最小 FAT12 ヘルパーを同梱し、MSX 形式で動作するディスクイメージを生成します。
* 格納するファイルとフォルダーを引数指定できます。フォルダーは再帰的に展開します。
* 容量不足時はデフォルトでエラー、`--allow-partial` を付ければ入るところまで格納し警告を出します。

## CLI (WIP)

command example:

```
python -m msxdisk.cli output.dsk data/extra.bin assets/ --ignore-ext .bak --allow-partial
```

## ブートセクタについて

`create_disk_image()` が作るディスクは **起動しない**。BPB は書くが、ブートコードは
書いていないためである。ファイルの読み書きはできるので、BASIC から

```
RUN"AUTOEXEC.BAS"
```

とすれば使える。

### 起動させたい場合

**実機や WebMSX でフォーマットしたブランクディスクを `DiskBuilder` に渡す。**
そのブートセクタごと引き継がれるので、起動可能なディスクになる。

```python
blank = Path("New_720KB_Disk.dsk").read_bytes()
builder = DiskBuilder(blank)
builder.add_files([...])
builder.write(Path("out.dsk"))
```

`DiskBuilder.from_default_blank()` を使うとゼロから作るので、この場合は起動しない。

### ブランクディスクを渡さない場合、何を書き換える必要があるか

自前で起動可能なブートセクタを作るなら、**個々に書き換える必要がある。**
実機のディスク(WebMSX がフォーマットしたもの)を読んで確認した並びは以下のとおり。

| 位置 | 実機の内容 | 説明 |
|---|---|---|
| 0x00-0x02 | `EB FE 90` | ジャンプ。`EB FE` はその場で無限ループだが、**ディスク ROM はここへ飛ばない**ので問題ない |
| 0x03-0x0A | `WMSX    ` | OEM 名。任意 |
| 0x0B-0x1D | BPB | 512 / 2 / 1 / 2 / 112 / 1440 / 0xF9 / 3 / 9 / 2 |
| **0x1E** | `18 10` (JR +0x10 → 0x30) | **ディスク ROM が呼ぶのはここ。** 最重要 |
| 0x20-0x25 | `VOL_ID` | ボリューム識別の文字列 |
| 0x26-0x2A | ボリューム番号 | |
| **0x30-0xB6** | **Z80 のブートコード 161 バイト** | ここが本体 |
| 0x1FE-0x1FF | `00 00` | **0x55AA は入らない** |

つまり最低限必要なのは:

1. **0x1E から始まるコード。** ディスク ROM が呼ぶ入口はここであって、0x00 のジャンプではない
2. そこから実際のブートコードへ繋ぐ

**やってはいけないこと:**

- **0x1E をゼロのまま残す。** ディスク ROM がゼロの列を実行して暴走する。
  実機(turbo R)で、画面に文字化けが出て BASIC が起動せず、STOP も効かなくなる症状が出た
- **末尾に `0x55AA` を書く。** PC の FAT の作法であって、MSX のディスクには入っていない。
  現状の `create_blank_2dd_image()` はこれを書いているが、実機の並びとは異なる
- **拡張ブート署名 `0x29` を書く。** これも実機の MSX ディスクには入っていない

起動させず、暴走もさせたくないだけであれば、**0x1E に `C9` (RET) を 1 バイト置けばよい。**
呼ばれても即座に戻るので、BASIC は正常に起動する。
