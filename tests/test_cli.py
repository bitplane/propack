import struct

import pytest

from propack import pack, unpack
from propack.cli import main
from propack.crc import crc16


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("destination", ["default", "explicit", "symlink", "hardlink"])
def test_pack_preserves_input_on_output_collision(tmp_path, capsys, method, destination):
    source = tmp_path / f"asset.rnc{method}"
    raw = b"original contents"
    source.write_bytes(raw)
    argv = ["pack", str(source), "-m", str(method)]
    if destination != "default":
        output = source
        if destination in ("symlink", "hardlink"):
            output = tmp_path / "alias"
            if destination == "symlink":
                output.symlink_to(source)
            else:
                output.hardlink_to(source)
        argv.append(str(output))

    assert main(argv) == 1
    assert "must not overwrite" in capsys.readouterr().err
    assert source.read_bytes() == raw


def test_pack_default_output(tmp_path):
    source = tmp_path / "asset.bin"
    raw = b"original contents"
    source.write_bytes(raw)

    assert main(["pack", str(source)]) == 0
    assert source.read_bytes() == raw
    assert unpack(source.with_suffix(".rnc1").read_bytes()) == raw


@pytest.mark.parametrize("command", ["pack", "p"])
@pytest.mark.parametrize("unpack_command", ["unpack", "u"])
def test_file_commands_accept_options_between_paths(tmp_path, command, unpack_command):
    source = tmp_path / "asset.bin"
    packed = tmp_path / "asset.rnc2"
    output = tmp_path / "restored.bin"
    raw = b"original contents"
    source.write_bytes(raw)

    assert main([command, str(source), "-m", "2", "-k", "0x1234", str(packed)]) == 0
    assert main([unpack_command, str(packed), "-k", "0x1234", str(output)]) == 0
    assert output.read_bytes() == raw


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("destination", ["explicit", "symlink", "hardlink", "default_symlink", "default_hardlink"])
def test_unpack_preserves_input_on_output_collision(tmp_path, capsys, method, destination):
    source = tmp_path / f"asset.rnc{method}"
    packed = pack(b"original contents", method=method)
    source.write_bytes(packed)
    argv = ["unpack", str(source)]
    output = source
    if destination != "explicit":
        output = source.with_suffix("") if destination.startswith("default_") else tmp_path / "alias"
        if destination.endswith("symlink"):
            output.symlink_to(source)
        else:
            output.hardlink_to(source)
    if not destination.startswith("default_"):
        argv.append(str(output))

    assert main(argv) == 1
    assert "must not overwrite" in capsys.readouterr().err
    assert source.read_bytes() == packed


@pytest.mark.parametrize("suffix", [".rnc1", ""])
def test_unpack_default_output(tmp_path, suffix):
    source = tmp_path / f"asset{suffix}"
    raw = b"original contents"
    packed = pack(raw)
    source.write_bytes(packed)

    assert main(["unpack", str(source)]) == 0
    assert source.read_bytes() == packed
    output = source.with_suffix("") if suffix else source.with_suffix(".unpacked")
    assert output.read_bytes() == raw


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("link", ["symlink", "hardlink"])
def test_extract_preserves_input_on_output_collision(tmp_path, capsys, method, link):
    source = tmp_path / "rom.bin"
    packed = pack(b"embedded contents", method=method)
    source.write_bytes(packed)
    output = tmp_path / "rom.00000000.bin"
    if link == "symlink":
        output.symlink_to(source)
    else:
        output.hardlink_to(source)

    assert main(["extract", str(source), str(tmp_path)]) == 1
    assert "must not overwrite" in capsys.readouterr().err
    assert source.read_bytes() == packed


def test_extract_skips_invalid_match_and_continues(tmp_path):
    payload = bytes.fromhex("3000")
    malformed = struct.pack(">3sBIIHHBB", b"RNC", 2, 2, 2, 0, crc16(payload), 0, 1) + payload
    raw = b"valid later block"
    source = tmp_path / "rom.bin"
    source.write_bytes(malformed + pack(raw, method=2))
    dest = tmp_path / "extracted"

    assert main(["extract", str(source), str(dest)]) == 0
    assert [p.name for p in dest.iterdir()] == [f"rom.{len(malformed):08X}.bin"]
    assert (dest / f"rom.{len(malformed):08X}.bin").read_bytes() == raw


@pytest.mark.parametrize("option", [None, "-o", "--output"])
@pytest.mark.parametrize("command", ["extract", "e"])
def test_extract_output_directory(tmp_path, option, command):
    raw = b"embedded data"
    source = tmp_path / "rom.bin"
    source.write_bytes(b"prefix" + pack(raw))
    dest = tmp_path / "output"
    argv = [command, str(source)]
    if option:
        argv.append(option)
    argv.append(str(dest))

    assert main(argv) == 0
    assert (dest / "rom.00000006.bin").read_bytes() == raw


def test_extract_default_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = b"embedded data"
    source = tmp_path / "rom.bin"
    source.write_bytes(pack(raw))

    assert main(["extract", str(source)]) == 0
    assert (tmp_path / "rom.00000000.bin").read_bytes() == raw


def test_extract_rejects_conflicting_output_directories(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["extract", "rom.bin", str(tmp_path / "one"), "-o", str(tmp_path / "two")])

    assert exc.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
