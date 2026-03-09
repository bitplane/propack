from pathlib import Path

import pytest

from propack import parse_header, unpack

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
