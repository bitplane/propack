import argparse
import sys
from pathlib import Path

from propack.constants import HEADER_SIZE, RNC_SIGNATURE
from propack.header import parse_header
from propack.unpack import unpack


def cmd_unpack(args):
    data = args.input.read_bytes()

    try:
        result = unpack(data, key=args.key)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    output = args.output
    if output is None:
        output = args.input.with_suffix("")
        if output == args.input:
            output = args.input.with_suffix(".unpacked")

    output.write_bytes(result)
    print(f"unpacked {len(data)} -> {len(result)} bytes to {output}")
    return 0


def cmd_info(args):
    data = args.input.read_bytes()

    try:
        header = parse_header(data)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"file:          {args.input}")
    print(f"method:        {header.method}")
    print(f"packed size:   {header.packed_size}")
    print(f"unpacked size: {header.unpacked_size}")
    print(f"packed CRC:    0x{header.packed_crc:04X}")
    print(f"unpacked CRC:  0x{header.unpacked_crc:04X}")
    print(f"leeway:        {header.leeway}")
    print(f"chunks:        {header.chunk_count}")
    ratio = header.packed_size / header.unpacked_size * 100 if header.unpacked_size else 0
    print(f"ratio:         {ratio:.1f}%")
    return 0


def cmd_scan(args):
    data = args.input.read_bytes()
    found = 0

    for i in range(len(data) - HEADER_SIZE):
        if data[i : i + 3] == RNC_SIGNATURE and data[i + 3] in (1, 2):
            try:
                header = parse_header(data[i:])
                method = header.method
                unpacked = header.unpacked_size
                packed = header.packed_size
                print(f"  offset 0x{i:08X}: method {method}, " f"{packed} -> {unpacked} bytes")
                found += 1
            except ValueError:
                pass

    if not found:
        print("no RNC data found")
    else:
        print(f"{found} RNC block(s) found")
    return 0


def cmd_extract(args):
    data = args.input.read_bytes()
    found = 0
    dest = args.output or Path(".")

    for i in range(len(data) - HEADER_SIZE):
        if data[i : i + 3] == RNC_SIGNATURE and data[i + 3] in (1, 2):
            try:
                header = parse_header(data[i:])
                chunk = data[i : i + HEADER_SIZE + header.packed_size]
                result = unpack(chunk, key=args.key)

                dest.mkdir(parents=True, exist_ok=True)
                out_path = dest / f"{args.input.stem}.{i:08X}.bin"
                out_path.write_bytes(result)
                print(f"  extracted 0x{i:08X} -> {out_path} ({len(result)} bytes)")
                found += 1
            except ValueError:
                pass

    if not found:
        print("no RNC data found")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="propack",
        description="RNC ProPack compression tool",
    )
    sub = parser.add_subparsers(dest="command")

    p_unpack = sub.add_parser("unpack", aliases=["u"], help="decompress a file")
    p_unpack.add_argument("input", type=Path, help="input file")
    p_unpack.add_argument("output", type=Path, nargs="?", help="output file")
    p_unpack.add_argument("-k", "--key", type=lambda x: int(x, 0), default=0, help="encryption key")
    p_unpack.set_defaults(func=cmd_unpack)

    p_info = sub.add_parser("info", aliases=["i"], help="show file info")
    p_info.add_argument("input", type=Path, help="input file")
    p_info.set_defaults(func=cmd_info)

    p_scan = sub.add_parser("scan", aliases=["s"], help="scan for embedded RNC data")
    p_scan.add_argument("input", type=Path, help="input file")
    p_scan.set_defaults(func=cmd_scan)

    p_extract = sub.add_parser("extract", aliases=["e"], help="scan and extract embedded RNC data")
    p_extract.add_argument("input", type=Path, help="input file")
    p_extract.add_argument("output", type=Path, nargs="?", help="output directory")
    p_extract.add_argument("-k", "--key", type=lambda x: int(x, 0), default=0, help="encryption key")
    p_extract.set_defaults(func=cmd_extract)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
