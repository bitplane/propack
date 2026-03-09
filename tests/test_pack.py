from pathlib import Path

import pytest

from propack import parse_header, unpack
from propack.pack import pack

FIXTURES = Path(__file__).parent / "fixtures"


def test_roundtrip_m1_pack1():
    raw = (FIXTURES / "pack1.expected").read_bytes()
    packed = pack(raw, method=1)
    assert unpack(packed) == raw


def test_roundtrip_m2_pack1():
    raw = (FIXTURES / "pack1.expected").read_bytes()
    packed = pack(raw, method=2)
    assert unpack(packed) == raw


def test_roundtrip_m1_pack2():
    raw = (FIXTURES / "pack2.expected").read_bytes()
    packed = pack(raw, method=1)
    assert unpack(packed) == raw


def test_roundtrip_m2_pack2():
    raw = (FIXTURES / "pack2.expected").read_bytes()
    packed = pack(raw, method=2)
    assert unpack(packed) == raw


def test_roundtrip_m1_100():
    raw = (FIXTURES / "100.expected").read_bytes()
    packed = pack(raw, method=1)
    assert unpack(packed) == raw


def test_header_after_pack():
    raw = (FIXTURES / "pack1.expected").read_bytes()
    packed = pack(raw, method=1)
    h = parse_header(packed)
    assert h.method == 1
    assert h.unpacked_size == len(raw)


def test_pack_all_zeros():
    raw = b"\x00" * 4096
    for method in (1, 2):
        packed = pack(raw, method=method)
        assert unpack(packed) == raw
        assert len(packed) < len(raw)


def test_pack_repeated_byte():
    raw = b"\xaa" * 1000
    packed = pack(raw, method=2)
    assert unpack(packed) == raw


def test_pack_invalid_method():
    with pytest.raises(ValueError, match="method"):
        pack(b"data", method=3)


def test_pack_empty():
    with pytest.raises(ValueError, match="empty"):
        pack(b"", method=1)
