import pytest

from tools.release_gate import pr_errors, release_errors
from tools.versioning import latest_tag

TAGS = ["v1.0.0", "v1.1.0", "v1.1.1", "not-a-version", "v2.0.0-rc1"]


def test_latest_tag_ignores_non_versions():
    assert latest_tag(TAGS) == "v1.1.1"
    assert latest_tag([]) is None


def test_release_branch_matching_newer_version_passes():
    assert pr_errors("release/v1.2.0", "1.2.0", "1.2.0", TAGS) == []


def test_first_release_with_no_tags_passes():
    assert pr_errors("release/v1.1.0", "1.1.0", "1.1.0", []) == []
    assert release_errors("1.1.0", "1.1.0", []) == []


def test_release_branch_name_must_match_version():
    errs = pr_errors("release/v1.3.0", "1.2.0", "1.2.0", TAGS)
    assert any("does not match" in e for e in errs)


def test_version_must_be_higher_than_latest_tag():
    errs = pr_errors("release/v1.1.0", "1.1.0", "1.1.0", TAGS)
    assert any("not higher" in e for e in errs)


def test_hotfix_branch_allowed_with_patch_bump():
    assert pr_errors("fix/null-crash", "1.1.2", "1.1.2", TAGS) == []
    assert any("not higher" in e for e in pr_errors("fix/null-crash", "1.1.1", "1.1.1", TAGS))


@pytest.mark.parametrize("head", ["dev", "feature/x", "chore/docs", "refactor/y", "main", ""])
def test_other_branches_rejected(head):
    errs = pr_errors(head, "1.2.0", "1.2.0", TAGS)
    assert any("must come from" in e for e in errs)


def test_version_files_must_agree():
    errs = pr_errors("release/v1.2.0", "1.2.0", "1.1.0", TAGS)
    assert any("mismatch" in e for e in errs)


def test_release_fails_when_tag_exists():
    errs = release_errors("1.1.1", "1.1.1", TAGS)
    assert any("already exists" in e for e in errs)


def test_release_passes_for_new_version():
    assert release_errors("1.2.0", "1.2.0", TAGS) == []
