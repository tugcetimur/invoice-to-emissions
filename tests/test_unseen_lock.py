"""The unseen UK electricity set must stay exactly as it was locked.

data/uk_electricity/unseen-sha256.txt lists the SHA-256 of every unseen PDF (made with
`shasum -a 256`). These tests fail if a file is changed, removed, or added without renewing
the lock. Renewing the lock is a commit of its own, so its date shows in the git history.
"""

import hashlib
import re
from pathlib import Path

import pytest

LOCK = Path("data/uk_electricity/unseen-sha256.txt")
UNSEEN = Path("data/uk_electricity/unseen")
LINE = re.compile(r"^([0-9a-f]{64}) [ *](.+)$")


def read_lock():
    entries = []
    for number, line in enumerate(LOCK.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = LINE.match(line)
        assert match, f"line {number} of {LOCK} is not in the 'hash  path' format"
        entries.append((match.group(2), match.group(1)))
    return entries


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


ENTRIES = read_lock()


@pytest.mark.parametrize("path, digest", ENTRIES, ids=[path.split("/", 3)[-1] for path, _ in ENTRIES])
def test_a_locked_file_is_unchanged(path, digest):
    assert Path(path).exists(), f"{path} is in the lock but missing on disk"
    assert sha256(path) == digest, f"{path} was changed after it was locked"


def test_no_unseen_pdf_was_added_or_removed():
    on_disk = {path.as_posix() for path in UNSEEN.rglob("*.pdf")}
    locked = {path for path, _ in ENTRIES}
    assert on_disk == locked, f"not locked: {sorted(on_disk - locked)}; locked but missing: {sorted(locked - on_disk)}"


def test_the_lock_lists_each_file_once():
    paths = [path for path, _ in ENTRIES]
    assert len(paths) == len(set(paths))
