import struct
from pathlib import Path

import pytest

from propack import pack, parse_header, unpack
from propack.crc import crc16

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(params=["pack1", "pack2", "100"])
def rnc1_fixture(request):
    name = request.param
    packed = (FIXTURES / f"{name}.rnc1").read_bytes()
    expected = (FIXTURES / f"{name}.expected").read_bytes()
    return packed, expected


def test_unpack_method1(rnc1_fixture):
    packed, expected = rnc1_fixture
    assert unpack(packed) == expected


@pytest.fixture(params=["pack1", "pack2"])
def rnc2_fixture(request):
    name = request.param
    packed = (FIXTURES / f"{name}.rnc2").read_bytes()
    expected = (FIXTURES / f"{name}_m2.expected").read_bytes()
    return packed, expected


def test_unpack_method2(rnc2_fixture):
    packed, expected = rnc2_fixture
    assert unpack(packed) == expected


def test_header_fields():
    data = (FIXTURES / "pack1.rnc1").read_bytes()
    h = parse_header(data)
    assert h.method == 1
    assert h.unpacked_size == 1024
    assert h.packed_size == 955


def test_methods_produce_same_output():
    m1 = unpack((FIXTURES / "pack1.rnc1").read_bytes())
    m2 = unpack((FIXTURES / "pack1.rnc2").read_bytes())
    assert m1 == m2


def test_invalid_signature():
    with pytest.raises(ValueError, match="invalid RNC signature"):
        unpack(b"XXX\x01" + b"\x00" * 14)


def test_truncated_header():
    with pytest.raises(ValueError, match="too short"):
        unpack(b"RNC\x01" + b"\x00" * 5)


@pytest.mark.parametrize("method", [1, 2])
def test_truncated_payload_raises_value_error(method):
    data = bytearray((FIXTURES / f"pack1.rnc{method}").read_bytes()[:28])
    payload_size = len(data) - 18
    struct.pack_into(">I", data, 8, payload_size)
    struct.pack_into(">H", data, 14, crc16(data[18:]))

    with pytest.raises(ValueError, match="unexpected end of packed data"):
        unpack(data)


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("raw", [b"abc", bytes(range(20)), b"abab", b"a" * 6, b"a" * 30, b"hello world" * 10])
def test_output_cannot_exceed_declared_size(method, raw):
    data = bytearray(pack(raw, method=method))
    # Size is outside the CRC-covered payload, so both CRCs remain valid.
    struct.pack_into(">I", data, 4, len(raw) - 1)

    with pytest.raises(ValueError, match="exceeds declared size"):
        unpack(data)


@pytest.mark.parametrize("method", [1, 2])
def test_output_shorter_than_declared_size_is_rejected(method):
    data = bytearray(pack(b"hello world", method=method))
    struct.pack_into(">I", data, 4, 12)

    with pytest.raises(ValueError):
        unpack(data)


@pytest.mark.parametrize(
    "method,payload,size",
    [
        (1, bytes.fromhex("8408114200000000"), 2),
        (2, bytes.fromhex("3000"), 2),  # short match
        (2, bytes.fromhex("3800"), 3),  # three-byte match
        (2, bytes.fromhex("2000"), 4),  # medium match
        (2, bytes.fromhex("3c0100"), 9),  # long match
    ],
)
def test_match_before_start_of_output_raises_value_error(method, payload, size):
    # Every stream starts with a match at distance one, before any literals.
    data = struct.pack(">3sBIIHHBB", b"RNC", method, size, len(payload), 0, crc16(payload), 0, 1) + payload

    with pytest.raises(ValueError, match="invalid match offset"):
        unpack(data)


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("raw", [b"a" * 100, b"abcd" * 100])
def test_overlapping_matches_remain_valid(method, raw):
    assert unpack(pack(raw, method=method)) == raw
