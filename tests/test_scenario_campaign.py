from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/generate_scenarios.py"


def load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_scenarios_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scenario generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_exclusive_ledger_lock_is_created_and_removed(tmp_path: Path) -> None:
    module = load_generator_module()
    lock_path = tmp_path / "ledger.lock"
    with module.exclusive_file_lock(lock_path):
        assert lock_path.is_file()
        assert f"pid={module.os.getpid()}" in lock_path.read_text(encoding="utf-8")
    assert not lock_path.exists()


def test_f0_and_f1_parallel_qualification_records_are_valid() -> None:
    module = load_generator_module()
    module.assert_parallel_qualification("F0")
    module.assert_parallel_qualification("F1")
