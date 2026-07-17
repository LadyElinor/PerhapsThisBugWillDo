from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]
WEEVIL_ROOT = REPO_ROOT / "weevil-lunar"


def _doc_base(doc: Path) -> Path:
    return WEEVIL_ROOT if WEEVIL_ROOT in doc.parents else REPO_ROOT


def test_workflow_is_discoverable_at_repo_root():
    workflow = REPO_ROOT / ".github" / "workflows" / "validate-and-benchmark.yml"
    assert workflow.exists(), f"Missing discoverable workflow at {workflow}"


def test_readme_relative_links_resolve_for_known_repo_files():
    targets = [REPO_ROOT / "README.md", WEEVIL_ROOT / "README.md", WEEVIL_ROOT / "docs" / "simulation_governance.md"]
    pattern = re.compile(r"(?P<path>(?:\.\.?/)+[^\s`)>]+|\.github/workflows/[^\s`)>]+|(?:weevil-lunar/)?(?:docs|specs|icd|cad|verification|results|models)/[^\s`)>]+\.(?:md|csv|json|yaml|yml|py|cff|txt)|(?:LICENSE|CITATION\.cff))")
    missing: list[str] = []

    for doc in targets:
        text = doc.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            rel = match.group("path")
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.start())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            if rel.startswith("http"):
                continue
            if ":\\" in rel:
                missing.append(f"{doc.relative_to(REPO_ROOT)} -> absolute-path-leak:{rel}")
                continue
            base = _doc_base(doc)
            candidate = (doc.parent / rel).resolve() if rel.startswith(".") else (base / rel).resolve()
            if not candidate.exists():
                if "may be absent in a fresh clone" in line or "not yet committed in this clone" in line:
                    continue
                missing.append(f"{doc.relative_to(REPO_ROOT)} -> {rel}")

    assert not missing, "Dangling or leaking references found:\n" + "\n".join(sorted(set(missing)))
