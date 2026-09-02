from pathlib import Path

import pytest

from propack import parse_header, unpack
from propack.constants import PACK_BLOCK_SIZE
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


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("size", [PACK_BLOCK_SIZE, PACK_BLOCK_SIZE + 1, PACK_BLOCK_SIZE * 2 + 17])
def test_encrypted_roundtrip_across_chunk_boundaries(method, size):
    raw = bytes((i * 37 + 11) & 0xFF for i in range(size))
    key = 0x1234

    packed = pack(raw, method=method, key=key)

    assert unpack(packed, key=key) == raw


@pytest.mark.parametrize("size", [13, 17, 29])
def test_encrypted_method2_literal_runs(size):
    raw = bytes(range(size))
    key = 0x1234

    packed = pack(raw, method=2, key=key)

    assert unpack(packed, key=key) == raw


def test_pack_invalid_method():
    with pytest.raises(ValueError, match="method"):
        pack(b"data", method=3)


def test_pack_empty():
    with pytest.raises(ValueError, match="empty"):
        pack(b"", method=1)
