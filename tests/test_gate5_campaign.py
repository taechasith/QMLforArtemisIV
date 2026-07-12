from __future__ import annotations

import json
from pathlib import Path

import pytest

import openqfuel.gate5_campaign as campaign_module
from openqfuel.gate5 import validate_development_output_path
from openqfuel.gate5_campaign import (
    CANDIDATE_IDS,
    QML_IDS,
    CampaignTask,
    _control_tasks_for_rung,
    _rank_one,
    campaign_lock,
    conservative_task_wall_time,
    freeze_task_authorization,
    initial_campaign_tasks,
    load_authorized_tasks,
    matched_control_tasks,
    representative_benchmark_tasks,
    run_campaign_benchmark,
    seed_rerun_tasks,
    task_output_dir,
    task_terminal_result,
    validate_task,
    verify_scientific_environment,
)


ROOT = Path(__file__).resolve().parents[1]


def test_initial_campaign_expands_only_exact_matched_control_views() -> None:
    tasks = initial_campaign_tasks(ROOT)
    assert len(tasks) == 450
    assert len({task.key for task in tasks}) == len(tasks)

    qml = [task for task in tasks if task.family_id in QML_IDS]
    controls = [task for task in tasks if task.candidate_role != "primary_candidate"]
    assert len(qml) == 90
    assert len(controls) == 180
    control_keys = {
        (task.family_id, task.trial_order, task.matched_qubits) for task in controls
    }
    for task in qml:
        assert task.matched_qubits in {4, 6, 8}
        assert ("A01", task.trial_order, task.matched_qubits) in control_keys
        assert ("C05", task.trial_order, task.matched_qubits) in control_keys


def test_later_matched_controls_follow_qml_rung_and_deduplicate() -> None:
    qml = [
        CampaignTask(
            "tuning",
            "Q01",
            "quantum_kernel",
            "Q01-T01",
            1,
            rung_samples=256,
            matched_qubits=4,
        ),
        CampaignTask(
            "tuning",
            "Q02",
            "variational_quantum_regressor",
            "Q02-T01",
            1,
            rung_samples=256,
            matched_qubits=4,
        ),
        CampaignTask(
            "tuning",
            "Q03",
            "hybrid_quantum_residual",
            "Q03-T01",
            1,
            rung_samples=256,
            matched_qubits=8,
        ),
    ]
    controls = matched_control_tasks(ROOT, qml, stage="tuning")
    assert len(controls) == 4
    assert {task.rung_samples for task in controls} == {256}
    shared = [task for task in controls if task.matched_qubits == 4]
    assert {task.control_for for task in shared} == {"Q01;Q02"}


def test_representative_benchmark_is_outcome_blind_and_bounded() -> None:
    tasks = representative_benchmark_tasks(ROOT)
    assert len(tasks) == 10
    candidates = [task for task in tasks if task.candidate_role == "primary_candidate"]
    assert {task.trial_id for task in candidates} == {
        "C04-T02",
        "Q01-T04",
        "Q02-T07",
        "Q03-T14",
    }
    projected = [task for task in tasks if task.family_id != "C04"]
    assert {task.rung_samples for task in projected} == {1024}
    assert len([task for task in tasks if task.family_id in {"A01", "C05"}]) == 6


def test_incomplete_benchmark_remains_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = next(
        task for task in initial_campaign_tasks(ROOT) if task.family_id == "C01"
    )
    monkeypatch.setattr(campaign_module, "verify_campaign_contract", lambda root: None)
    monkeypatch.setattr(campaign_module, "initial_campaign_tasks", lambda root: [task])
    monkeypatch.setattr(
        campaign_module, "representative_benchmark_tasks", lambda root: [task]
    )
    monkeypatch.setattr(campaign_module, "_write_campaign_contract", lambda *args: None)
    monkeypatch.setattr(
        campaign_module, "freeze_task_authorization", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(campaign_module, "execute_tasks", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        campaign_module,
        "task_terminal_result",
        lambda *args: ("missing", None),
    )
    monkeypatch.setattr(campaign_module, "_task_measured_wall", lambda *args: None)

    with pytest.raises(RuntimeError, match="resume the benchmark"):
        run_campaign_benchmark(ROOT, tmp_path)

    assert (tmp_path / "benchmark_progress.json").is_file()
    assert not (tmp_path / "benchmark_audit.json").exists()


def test_resumed_benchmark_keeps_the_larger_checkpoint_time() -> None:
    assert conservative_task_wall_time(
        3.0, {"end_to_end_wall_time_s": 12.5}
    ) == pytest.approx(12.5)
    assert conservative_task_wall_time(
        14.0, {"end_to_end_wall_time_s": 12.5}
    ) == pytest.approx(14.0)


def test_seed_reruns_cover_twenty_frozen_indices_and_matched_controls() -> None:
    initial = initial_campaign_tasks(ROOT)
    finalists = []
    for family_id in CANDIDATE_IDS:
        candidates = [
            task
            for task in initial
            if task.family_id == family_id
            and task.candidate_role == "primary_candidate"
        ]
        task = candidates[0]
        if family_id in QML_IDS:
            task = CampaignTask(**{**task.__dict__, "rung_samples": 1024})
        finalists.append(task)

    tuned_controls = [
        task
        for task in initial
        if task.family_id in {"A01", "C05"}
        and task.matched_qubits
        in {qml.matched_qubits for qml in finalists if qml.family_id in QML_IDS}
    ][:2]
    tasks = seed_rerun_tasks(ROOT, finalists, tuned_controls, seeds=20)
    assert len({task.key for task in tasks}) == len(tasks)
    candidate_tasks = [
        task
        for task in tasks
        if task.family_id in CANDIDATE_IDS
        and task.candidate_role == "primary_candidate"
    ]
    assert len(candidate_tasks) == 20 * len(CANDIDATE_IDS)
    assert {task.seed_index for task in candidate_tasks} == set(range(1, 21))

    controls = [task for task in tasks if task.candidate_role != "primary_candidate"]
    for qml in [task for task in candidate_tasks if task.family_id in QML_IDS]:
        assert any(
            control.family_id == "A01"
            and control.trial_order == qml.trial_order
            and control.matched_qubits == qml.matched_qubits
            and control.seed_index == qml.seed_index
            for control in controls
        )
        assert any(
            control.family_id == "C05"
            and control.view == "compressed_c05"
            and control.trial_order == qml.trial_order
            and control.matched_qubits == qml.matched_qubits
            and control.seed_index == qml.seed_index
            for control in controls
        )


def test_seed_reruns_require_exactly_twenty_and_merge_control_roles() -> None:
    initial = initial_campaign_tasks(ROOT)
    qml = next(task for task in initial if task.family_id == "Q01")
    qml = CampaignTask(**{**qml.__dict__, "rung_samples": 1024})
    paired = next(
        task
        for task in initial
        if task.family_id == "A01"
        and task.trial_order == qml.trial_order
        and task.matched_qubits == qml.matched_qubits
    )
    paired = CampaignTask(
        **{
            **paired.__dict__,
            "rung_samples": 1024,
            "advancement_basis": "control_ranked",
            "control_for": "Q01",
        }
    )
    with pytest.raises(ValueError, match="exactly 20"):
        seed_rerun_tasks(ROOT, [qml], [paired], seeds=19)
    tasks = seed_rerun_tasks(ROOT, [qml], [paired], seeds=20)
    merged = next(
        task for task in tasks if task.family_id == "A01" and task.seed_index == 1
    )
    assert merged.advancement_basis == "control_ranked_and_qml_matched"


def test_task_metadata_validation_rejects_tampering() -> None:
    task = next(
        task for task in initial_campaign_tasks(ROOT) if task.family_id == "Q01"
    )
    validate_task(ROOT, task)
    tampered = CampaignTask(**{**task.__dict__, "model_family": "extra_trees"})
    with pytest.raises(PermissionError, match="frozen trial"):
        validate_task(ROOT, tampered)


def test_scientific_environment_must_match_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = campaign_module.expected_scientific_versions()
    monkeypatch.setattr(
        campaign_module.importlib.metadata,
        "version",
        lambda name: expected[name],
    )
    assert verify_scientific_environment(ROOT) == expected
    monkeypatch.setattr(
        campaign_module.importlib.metadata,
        "version",
        lambda name: "0.0" if name == "numpy" else expected[name],
    )
    with pytest.raises(PermissionError, match="differs from uv.lock"):
        verify_scientific_environment(ROOT)


def test_authorization_parent_is_immutable_and_verified(tmp_path: Path) -> None:
    task = next(
        task for task in initial_campaign_tasks(ROOT) if task.family_id == "C01"
    )
    path = tmp_path / "tasks.csv"
    freeze_task_authorization(ROOT, path, [task], parent_digest="parent-a")
    assert load_authorized_tasks(path, ROOT, expected_parent_digest="parent-a") == [
        task
    ]
    with pytest.raises(PermissionError, match="parent mismatch"):
        load_authorized_tasks(path, ROOT, expected_parent_digest="parent-b")
    sidecar = json.loads(path.with_suffix(".csv.json").read_text(encoding="utf-8"))
    sidecar["parent_digest"] = "tampered"
    path.with_suffix(".csv.json").write_text(json.dumps(sidecar), encoding="utf-8")
    with pytest.raises(PermissionError, match="parent mismatch"):
        load_authorized_tasks(path, ROOT, expected_parent_digest="parent-a")


def test_campaign_and_terminal_task_locks_are_fail_closed(tmp_path: Path) -> None:
    with campaign_lock(tmp_path):
        with pytest.raises(RuntimeError, match="already locked"):
            with campaign_lock(tmp_path):
                pass

    task = next(
        task for task in initial_campaign_tasks(ROOT) if task.family_id == "C01"
    )
    assert task_terminal_result(ROOT, tmp_path, task) == ("missing", None)
    failure_path = task_output_dir(tmp_path, task) / "failure.json"
    failure_path.parent.mkdir(parents=True)
    failure_path.write_text(
        json.dumps(
            {
                "source_commit": campaign_module._head(ROOT),
                "task": task.__dict__,
            }
        ),
        encoding="utf-8",
    )
    assert task_terminal_result(ROOT, tmp_path, task)[0] == "failed"

    failure_path.write_text(
        json.dumps(
            {
                "source_commit": campaign_module._head(ROOT),
                "task": {**task.__dict__, "trial_id": "C01-T02"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(PermissionError, match="failure identity mismatch"):
        task_terminal_result(ROOT, tmp_path, task)


def test_development_outputs_reject_the_final_payload_root() -> None:
    with pytest.raises(PermissionError, match="final payload root"):
        validate_development_output_path(
            ROOT, ROOT / "data/locked/phase1/gate5-results"
        )


def test_control_halving_is_independent_per_dimension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tasks = [
        task
        for task in initial_campaign_tasks(ROOT)
        if task.family_id == "A01" and task.matched_qubits == 4
    ]

    def terminal(root: Path, output: Path, task: CampaignTask):
        trial = campaign_module.load_trial(root, task.trial_id)
        return (
            "complete",
            {
                "eligible_to_advance": True,
                "pooled_oof_nrmse": task.trial_order / 100.0,
                "mean_regret_m_s": 1.0,
                "matched_qubits": 4,
                "trial": {
                    "trial_id": trial.trial_id,
                    "model_family": trial.model_family,
                    "parameters": trial.parameters,
                },
            },
        )

    monkeypatch.setattr(campaign_module, "task_terminal_result", terminal)
    selected, rankings = _control_tasks_for_rung(ROOT, tmp_path, tasks, 128, 256)
    assert len(selected) == 15
    assert {task.matched_qubits for task in selected} == {4}
    assert sum(row["selected_for_next_rung"] for row in rankings) == 15


def test_selection_rejects_an_interrupted_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = next(
        task for task in initial_campaign_tasks(ROOT) if task.family_id == "C01"
    )
    monkeypatch.setattr(
        campaign_module,
        "task_terminal_result",
        lambda *args: ("missing", None),
    )
    with pytest.raises(RuntimeError, match="interrupted stage"):
        _rank_one(ROOT, tmp_path, [task])
