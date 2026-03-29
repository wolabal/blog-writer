from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_hardcoded_workspace_drive_paths():
    tracked = [
        ROOT / "blog.cmd",
        ROOT / "README.md",
        ROOT / "dashboard" / "README.md",
        ROOT / "blog_engine_cli.py",
    ]
    bad_tokens = ["D:\\workspace\\blog-writer", "D:/workspace/blog-writer"]

    for path in tracked:
        text = path.read_text(encoding="utf-8")
        for token in bad_tokens:
            assert token not in text, f"{path} still contains {token}"


def test_readme_does_not_mark_unfinished_distribution_as_complete():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "코드 완료 | Instagram, X 배포" not in text


def test_readme_contains_release_verification_commands():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "python -m pytest tests -v" in text
    assert "python -m compileall blogwriter bots dashboard blog_engine_cli.py blog_runtime.py runtime_guard.py" in text
    assert "cd dashboard/frontend && npm run build" in text
