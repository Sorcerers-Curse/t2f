# t2f

`t2f` converts a text tree diagram into real files and directories.

It supports normal Unicode box-drawing characters and common mojibake variants.

## Features

- Creates nested directories and empty files from a tree diagram.
- Supports normal tree characters: `├──`, `└──`, `│`.
- Normalizes common mojibake sequences automatically.
- `--dry-run` mode for preview.
- `--force` mode to overwrite existing files with empty content.
- Rejects unsafe paths containing `..` or absolute path components.
- Tries the specified encoding first, then falls back to `cp1251`.

## Requirements

- Python 3.8+
- No third-party dependencies

## Usage

```bash
python t2f.py tree.txt
python t2f.py tree.txt -o ./generated
python t2f.py tree.txt --dry-run
python t2f.py tree.txt --force
python t2f.py tree.txt --encoding utf-8
