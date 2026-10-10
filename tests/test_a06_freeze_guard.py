"""The target stage must refuse to run unless the frozen calibration is committed."""
import subprocess

import pytest

a06 = pytest.importorskip("a06_targets")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    frozen = tmp_path / "results" / "frozen.json"
    frozen.parent.mkdir()
    monkeypatch.setattr(a06, "ROOT", tmp_path)
    monkeypatch.setattr(a06, "FROZEN", frozen)
    return tmp_path, frozen


def commit(root, msg="c"):
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", msg], cwd=root, check=True)


def test_missing_file_refuses(repo):
    root, frozen = repo
    (root / "x").write_text("x")
    commit(root)
    with pytest.raises(SystemExit):
        a06.assert_frozen_committed()


def test_uncommitted_file_refuses(repo):
    root, frozen = repo
    (root / "x").write_text("x")
    commit(root)
    frozen.write_text("{}")
    with pytest.raises(SystemExit):
        a06.assert_frozen_committed()


def test_modified_after_commit_refuses(repo):
    root, frozen = repo
    frozen.write_text("{}")
    commit(root)
    frozen.write_text('{"s_min": 1}')
    with pytest.raises(SystemExit):
        a06.assert_frozen_committed()


def test_committed_and_clean_passes(repo):
    root, frozen = repo
    frozen.write_text("{}")
    commit(root)
    a06.assert_frozen_committed()
