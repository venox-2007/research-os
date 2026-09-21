"""Security tests verifying hard containment boundaries and exploit rejection."""

from uuid import uuid4

import pytest

from backend.experiments.datasets import SecurityError, get_dataset_registry
from backend.experiments.models import ExperimentSpec
from backend.experiments.runner import get_experiment_runner


@pytest.mark.asyncio
async def test_rejects_unregistered_function() -> None:
    """Verify runner rejects any function not explicitly in the approved ExperimentRegistry."""
    runner = get_experiment_runner()
    spec = ExperimentSpec(
        experiment_id=uuid4(),
        title="Unauthorized Function Attack",
        hypothesis="Attacking execution layer",
        objective="Run unvetted code",
        function_name="arbitrary_unvetted_script",
        dataset_id="synthetic_regression",
    )
    result = await runner.run(spec)
    assert result.status == "rejected"
    assert "not in approved experimentregistry" in result.provenance.get("error", "").lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        "__import__('os').system('ls')",
        "eval('2+2')",
        "exec('import subprocess; subprocess.Popen()')",
        "os.system('calc')",
        "subprocess.run(['dir'])",
        "open('sensitive.txt', 'w')",
        "globals()['__builtins__']",
        "requests.get('http://attacker.com')",
        "urllib.request.urlopen('http://evil.com')",
        "httpx.get('http://malicious.com')",
        "socket.connect(('127.0.0.1', 80))",
    ],
)
async def test_rejects_prohibited_injection_payloads(payload: str) -> None:
    """Verify parameters containing dangerous tokens or commands are immediately rejected."""
    runner = get_experiment_runner()
    spec = ExperimentSpec(
        experiment_id=uuid4(),
        title="Injection Attempt Probe",
        hypothesis="Testing code injection filter",
        objective="Escape sandbox",
        function_name="linear_regression_benchmark",
        dataset_id="synthetic_regression",
        parameters={"alpha": 1.0, "injection_probe": payload},
    )
    result = await runner.run(spec)
    assert result.status == "rejected"
    assert "security policy violation" in result.provenance.get("error", "").lower()


def test_rejects_dataset_path_traversal() -> None:
    """Verify dataset registry strictly blocks directory traversal attempts."""
    datasets = get_dataset_registry()

    with pytest.raises(SecurityError):
        datasets._safe_resolve("../../etc/passwd")

    with pytest.raises(SecurityError):
        datasets._safe_resolve("../../../Windows/System32/cmd.exe")

    with pytest.raises(SecurityError):
        datasets._safe_resolve("C:\\Windows\\System32\\cmd.exe")


@pytest.mark.asyncio
async def test_rejects_traversal_in_dataset_id() -> None:
    """Verify runner rejects dataset_id containing path traversal."""
    runner = get_experiment_runner()
    spec = ExperimentSpec(
        experiment_id=uuid4(),
        title="Dataset Path Traversal Probe",
        hypothesis="None",
        objective="None",
        function_name="linear_regression_benchmark",
        dataset_id="../../secret.csv",
    )
    result = await runner.run(spec)
    assert result.status in ("rejected", "failed")
