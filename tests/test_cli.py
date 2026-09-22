import pytest

from propack import unpack
from propack.cli import main


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
