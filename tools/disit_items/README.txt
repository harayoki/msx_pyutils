English version is available after the Japanese section.

## basic sc2 viewer

`basic_sc2_viewer.exe` は 複数の画像生データファイルとBASIC製のビューアーを収めたdskイメージを生成するツールです。
msx1pq_cli.exe が書き出したsc2を引数に渡すと、MSXエミュレーター等で実行できるdskイメージを生成します。
MSX2で起動した場合もMSX1の色味に近づけて表示する処理が入っています。
実際の2DDディスクに書き込めば実機でも実行可能と思われますが、動作確認はしていません。
将来的に入力ファイルとしてsc2の代わりにPNG画像を直接受け入れられるようになる予定です。
使い方は`basic_sc2_viewer.exe -h` でヘルプを参照してください。

※ WebMSXで動作確認しています。

## create sc2 32k rom

`create_sc2_32k_rom.exe` を使うと2枚のsc2ファイルを同梱したビューアー付きのROMを作る事ができます。dsk版より起動が早いです。
クイックなMSX1ドット絵共有にお使いください。なおROMデータは独自の調査により得た情報で
マシン語バイナリが動くフォーマットで作られていますが、実際に物理的なROMに焼いて動くかどうかは試せていないので分かりません。
使い方は`create_sc2_32k_rom.exe -h` でヘルプを参照してください。

※ WebMSXで動作確認しています。


---


## basic sc2 viewer

`basic_sc2_viewer.exe` is a tool that generates a DSK image containing multiple raw image data files and a BASIC viewer.
By passing the `.sc2`/`.sc5` files output by `msx1pq_cli.exe` as arguments, it creates a DSK image that can be executed on MSX emulators.
SC5 support is slated for deprecation, with a switch to planned SC4 support.
There are also plans to allow passing PNG images directly as inputs instead of only `.sc2` files.
It is assumed that writing the image to an actual 2DD disk will allow it to run on real hardware, but this has not been verified.
For usage, refer to the help by running `basic_sc2_viewer.exe -h`.
# Documentation
For more details, see the repository below.
https://github.com/harayoki/MMSXX_MSX1PaletteQuantizer
