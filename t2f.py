#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# t2f - convert a text tree diagram into real files and directories.
# Supports normal box-drawing characters and common mojibake variants.


import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional

MOJIBAKE_MAP = {
    'в”њ': '├',
    'в””': '└',
    'в”‚': '│',
    'в”Ђ': '─',
    'в”': '│',
}


def normalize_line(line: str) -> str:
    for bad, good in MOJIBAKE_MAP.items():
        line = line.replace(bad, good)
    return line


def parse_line(line: str) -> Optional[Tuple[int, str]]:
    line = normalize_line(line.rstrip('\n'))
    if not line.strip():
        return None

    for branch in ('├── ', '└── ', '├─ ', '└─ ', '┌── ', '└─ ', '├──', '└──'):
        idx = line.find(branch)
        if idx != -1:
            prefix = line[:idx]
            name = line[idx + len(branch):].strip()
            depth = len(prefix) // 4 + 1
            return depth, name

    stripped = line.strip()
    if stripped:
        return 0, stripped
    return None


def build_tree(entries: List[Tuple[int, str]]) -> List[Tuple[Path, bool]]:
    result: List[Tuple[Path, bool]] = []
    stack: List[Tuple[int, Path]] = []

    for i, (depth, name) in enumerate(entries):
        is_dir = name.endswith('/')

        if not is_dir and i + 1 < len(entries) and entries[i + 1][0] > depth:
            is_dir = True

        clean_name = name.rstrip('/')
        if not clean_name:
            continue

        while stack and stack[-1][0] >= depth:
            stack.pop()

        if stack:
            parent = stack[-1][1]
        else:
            parent = Path('.')

        path = parent / clean_name

        if is_dir:
            stack.append((depth, path))

        result.append((path, is_dir))

    return result


def safe_join(base: Path, rel: Path) -> Path:
    parts = []
    for part in rel.parts:
        if part == '..':
            raise ValueError(f"Path contains '..': {rel}")
        if part.startswith('/') or part.startswith('\\'):
            raise ValueError(f"Path is absolute: {rel}")
        parts.append(part)
    return base.joinpath(*parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Convert a text tree diagram into real files and directories.'
    )
    parser.add_argument('input', help='Input file with the tree diagram')
    parser.add_argument(
        '-o', '--output', default='.',
        help='Directory where the structure will be created (default: current directory)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Only print what would be created'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Overwrite existing files with empty content'
    )
    parser.add_argument(
        '--encoding', default='utf-8',
        help='Input file encoding (default: utf-8)'
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"Error: file not found: {input_path}")
        return 1

    try:
        text = input_path.read_text(encoding=args.encoding)
    except UnicodeDecodeError:
        try:
            text = input_path.read_text(encoding='cp1251')
        except Exception as exc:
            print(f"Could not read file: {exc}")
            return 1

    lines = text.splitlines()

    entries: List[Tuple[int, str]] = []
    for line in lines:
        parsed = parse_line(line)
        if parsed is not None:
            entries.append(parsed)

    if not entries:
        print("No tree elements found.")
        return 1

    try:
        tree = build_tree(entries)
    except Exception as exc:
        print(f"Error while building tree: {exc}")
        return 1

    output_dir = Path(args.output)
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    for rel_path, is_dir in tree:
        try:
            full_path = safe_join(output_dir, rel_path)
        except ValueError as exc:
            print(f"Skipping unsafe path {rel_path}: {exc}")
            continue

        if is_dir:
            if args.dry_run:
                print(f"[DIR]  {full_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
        else:
            if args.dry_run:
                print(f"[FILE] {full_path}")
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                if full_path.exists():
                    if args.force:
                        full_path.write_text('', encoding='utf-8')
                        print(f"Overwritten: {full_path}")
                    else:
                        print(f"Skipped (already exists): {full_path}")
                else:
                    full_path.touch()
                    print(f"Created: {full_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())