import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("status", [0, 1, 2, 5])
def test_coverage_script_preserves_pytest_exit_status(tmp_path, status):
    script = Path(__file__).resolve().parents[1] / "scripts" / "coverage.sh"
    bin_dir = tmp_path / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "activate").write_text('export PATH="$PWD/.venv/bin:$PATH"\n')
    pytest_stub = bin_dir / "pytest"
    pytest_stub.write_text(f"#!/bin/sh\necho 'Name Stmts Miss Cover Missing'\necho 'test output'\nexit {status}\n")
    pytest_stub.chmod(0o755)

    result = subprocess.run(["bash", str(script), "propack"], cwd=tmp_path, capture_output=True, text=True, check=False)

    assert result.returncode == status, result.stderr
    assert "test output" in result.stdout
    assert "test output" in (tmp_path / "htmlcov" / "coverage_report.txt").read_text()
    assert "test output" in (tmp_path / "htmlcov" / "missing_coverage.txt").read_text()
