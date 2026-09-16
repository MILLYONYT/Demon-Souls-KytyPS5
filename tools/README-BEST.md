# Build 32 LTO BEST binary baseline

The Windows release asset at [DemonSoulsKytyPS5](https://github.com/MILLYONYT/Demon-Souls-KytyPS5/releases/tag/DemonSoulsKytyPS5) is the verified working baseline. `build_from_best.py` verifies its SHA-256 before producing output. Without a patch, the output is byte for byte identical to the release ZIP, including the executable. This is an exact copy of the compiled build, not a compilation of its missing source.

```sh
python tools/build_from_best.py KytyPS5-Build32-LTO-BEST-copy.zip
```

For offline use, pass `--source path/to/KytyPS5-Build32-LTO-BEST.zip`. The expected SHA-256 is `b4c9aad01b22886beef0dda58d1978b8acfc5fe39577ed1a348fd34abc502dea`.

Future binary experiments can supply `--patch patches.json`. Each patch must name `kyty_emulator.exe` or `launcher.exe`, an integer byte offset, and equal-length original and replacement bytes in hexadecimal:

```json
{"patches":[{"member":"kyty_emulator.exe","offset":1234,"before":"0102","after":"0304"}]}
```

The script refuses a patch if the release checksum or the bytes at its offset differ. A patched ZIP is a separate candidate; always retain the unmodified release and test both at the same save and graphics settings. Byte patches cannot generally reconstruct the missing C++ source or guarantee equivalent behavior.
