from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_skill_scope_is_generic_pytest_requests():
    text = read("SKILL.md")

    assert "\\test-automation\\E10" not in text
    assert "for `python + pytest + requests`" in text


def test_pytest_workdir_docs_are_config_driven():
    core = read("doc/core_principles.md")
    maintenance = read("doc/mode_maintenance_pytest_driven.md")

    assert "config.json" in core
    assert "pytest.command_template" in maintenance


def test_preflight_docs_do_not_require_e10_marker():
    new_gate = read("doc/preflight_gates_new.md")
    maintenance_gate = read("doc/preflight_gates_maintenance.md")

    assert "test-automation/E10" not in new_gate
    assert "test-automation/E10" not in maintenance_gate
