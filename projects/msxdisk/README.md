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

出典: **MSX-Datapack**(アスキー) 第3部「MSX-DOS」3章「MSX-DOS の構造」
3.1「MSX-DOS の起動」(p.396〜397)。実機 MSX turbo R で動作確認済み。

### 起動の手順

1. ディスク ROM がブートセクタを **C000H〜C0FFH** へ転送する(**先頭 256 バイトだけ**)
2. **転送されたセクタの先頭が `EBH` か `E9H` でなければ、Disk BASIC が起動する**
3. 先頭が `EBH` / `E9H` なら **C01EH**(セクタの `0x1E`)が呼ばれる
   - **1 回目は CY をリセットした状態**
   - MSX-DOS の環境を初期化したあと、**2 回目は CY をセットした状態**
   - 標準では `RET NC` + ブートプログラムが置かれている。
     `RET NC` は「キャリーが立っていなければ戻る」ので、
     **1 回目は戻り、2 回目は素通りしてブートプログラムへ入る**
4. 標準のブートプログラムは `MSXDOS.SYS` を読み、無ければ Disk BASIC を起動する
5. **MSX-DOS が起動せず Disk BASIC が立ち上がったときは、`AUTOEXEC.BAS` があれば実行する**

#### 資料の表記について

資料には「先頭が `FBH` か `E9H` でなかったときは」とあるが、**`EBH` の誤りと考えられる。**

- 実物のディスクは `EB FE 90` で始まっており、これが「起動可能」と判定されて
  C01EH が呼ばれていた
- 先頭を `00` にしたら判定が外れ、Disk BASIC が起動して `AUTOEXEC.BAS` が実行された
- `FBH` は Z80 の `EI` 命令で、ジャンプ命令ではない。
  `EBH`(`JR`) / `E9H`(`JP (HL)`) と並ぶ位置づけとして不自然

### `AUTOEXEC.BAS` を自動実行させたいだけなら、ブートコードは要らない

上の手順 2 と 5 から、**ブートセクタが「起動できない」と判定されれば
Disk BASIC が起動し、`AUTOEXEC.BAS` が実行される。**

つまり**先頭バイトを `EBH` / `E9H` 以外にするだけでよい。**
ブートコードを書く必要も、他所から持ってくる必要もない。

### 現状の `create_blank_2dd_image()` の問題

いまの実装は先頭に `EB 3C 90` を書き、`0x1E` はゼロのままになっている。
これは**上記の手順で最も悪い組み合わせ**である。

- 先頭が `EBH` なので「起動可能」と判定され、C01EH が呼ばれる
- そこがゼロなので、ゼロの列を実行して**暴走する**

実機(turbo R)では、画面に文字化けが出て BASIC が起動せず、STOP も効かなくなった。

**修正は 1 バイト。** 先頭を `EBH`/`E9H` 以外にする。

```python
image[0:3] = b"\x00\x00\x00"   # EBH/E9H 以外なら何でもよい
```

念のため `0x1E` に `RET NC` (`0xD0`) を置いておくとより安全(実物と同じ作法)。

なお、起動可能なディスクにしたい場合は、**実機や WebMSX でフォーマットした
ブランクディスクを `DiskBuilder` に渡す。** そのブートセクタごと引き継がれる。

```python
blank = Path("New_720KB_Disk.dsk").read_bytes()
builder = DiskBuilder(blank)
builder.add_files([...])
builder.write(Path("out.dsk"))
```

`DiskBuilder.from_default_blank()` はゼロから作るので、この場合は上記の修正が要る。

### 実物のブートセクタの並び

実機/WebMSX がフォーマットしたディスクを読んだもの。

| 位置 | 内容 | 説明 |
|---|---|---|
| 0x00-0x02 | `EB FE 90` | `EB FE` はその場で無限ループだが、**ROM はここへ飛ばない** |
| 0x03-0x0A | `WMSX    ` | OEM 名。任意 |
| 0x0B-0x1D | BPB | 512 / 2 / 1 / 2 / 112 / 1440 / 0xF9 / 3 / 9 / 2 |
| **0x1E** | `18 10` (JR +0x10 → 0x30) | **C01EH。ROM が呼ぶのはここ** |
| 0x20-0x25 | `VOL_ID` | ボリューム識別の文字列 |
| 0x26-0x2A | ボリューム番号 | |
| **0x30-0xB6** | Z80 のブートコード 161 バイト | `RET NC` から始まる |
| 0x1FE-0x1FF | `00 00` | |

**現状の実装が書いている `0x55AA` と拡張ブート署名 `0x29` は、
実機の MSX ディスクには入っていない。** どちらも PC の FAT の作法である。
