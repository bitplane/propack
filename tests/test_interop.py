from pathlib import Path

import pytest

from propack import pack, parse_header, unpack

FIXTURES = Path(__file__).parent / "fixtures"
INPUTS = {
    "": b"A" * 12288 + b"B" * 100,
    "mixed-": bytes(range(101))
    + b"A" * 4000
    + bytes(range(150, 250))
    + b"B" * 8087
    + bytes(range(50, 151))
    + b"C" * 100,
}
KEY = 0x1234


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("case", INPUTS)
def test_unpack_upstream_encrypted_chunks(method, case):
    packed = (FIXTURES / f"upstream-encrypted-{case}m{method}.rnc").read_bytes()

    assert parse_header(packed).chunk_count == 2
    assert unpack(packed, key=KEY) == INPUTS[case]


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("case", INPUTS)
def test_pack_matches_independently_verified_encrypted_stream(method, case):
    # Golden streams were decoded by the upstream C tool, not our own unpacker.
    expected = (FIXTURES / f"verified-encrypted-{case}m{method}.rnc").read_bytes()

    assert pack(INPUTS[case], method=method, key=KEY) == expected
    assert unpack(expected, key=KEY) == INPUTS[case]
