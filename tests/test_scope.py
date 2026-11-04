"""R6 y R11: solo Python + scikit-learn + Implicit; sin deep learning ni agentes LLM."""

import re

from recsys.config import PROJECT_ROOT

FORBIDDEN = ("torch", "tensorflow", "keras", "jax", "transformers", "langchain", "langgraph")
REQUIRED = ("scikit-learn", "implicit")


def _requirement_names() -> set[str]:
    lines = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return {re.split(r"[<>=!~\[ ]", line)[0].lower() for line in lines if line.strip()}


def test_required_libraries_are_declared():
    assert set(REQUIRED) <= _requirement_names()


def test_no_deep_learning_dependencies():
    assert not set(FORBIDDEN) & _requirement_names()


def test_no_deep_learning_imports_in_source():
    pattern = re.compile(rf"^\s*(import|from)\s+({'|'.join(FORBIDDEN)})\b", re.MULTILINE)
    sources = [*(PROJECT_ROOT / "src").rglob("*.py"), *(PROJECT_ROOT / "scripts").glob("*.py")]
    offenders = [str(path) for path in sources if pattern.search(path.read_text(encoding="utf-8"))]
    assert offenders == []
