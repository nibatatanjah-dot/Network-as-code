"""Fast tests for source-of-truth invariants and generated config intent."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_data import validate  # noqa: E402


def test_source_of_truth_is_consistent():
    assert validate() == []


def test_renderer_generates_seven_devices():
    output = ROOT / "build" / "rendered"
    assert output.is_dir(), "Run scripts/render_configs.py before pytest."
    configs = list(output.glob("*.cfg"))
    assert len(configs) == 7


def test_guest_acl_blocks_internal_prefix():
    output = ROOT / "build" / "rendered" / "HQ-R1.cfg"
    assert output.exists(), "Run scripts/render_configs.py before pytest."
    config = output.read_text(encoding="utf-8")
    section = config.split("ip access-list extended GUEST-IN", 1)[1].split("!", 1)[0]
    assert "deny ip any 10.0.0.0 0.255.255.255 log" in section
    assert section.index("deny ip any 10.0.0.0 0.255.255.255 log") < section.index("permit tcp any any eq www")


def test_management_and_rogue_test_port_are_restricted():
    for name in ("HQ-SW1.cfg", "BR1-SW1.cfg", "BR2-SW1.cfg"):
        config = (ROOT / "build" / "rendered" / name).read_text(encoding="utf-8")
        assert "ip dhcp snooping vlan 10,30" in config
        assert "ip arp inspection vlan 10,30" in config
        port5 = config.split("interface FastEthernet0/5", 1)[1].split("!", 1)[0]
        assert "shutdown" in port5


def test_bad_change_injects_permit_before_guest_deny(tmp_path):
    source = ROOT / "build" / "rendered"
    assert source.is_dir(), "Run scripts/render_configs.py before pytest."
    output = tmp_path / "bad-change"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "make_bad_change.py"), "--source", str(source), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    config = (output / "HQ-R1.cfg").read_text(encoding="utf-8")
    section = config.split("ip access-list extended GUEST-IN", 1)[1].split("!", 1)[0]
    permit = "permit ip any 10.0.0.0 0.255.255.255"
    deny = "deny ip any 10.0.0.0 0.255.255.255 log"
    assert permit in section
    assert deny in section
    assert section.index(permit) < section.index(deny)
    # Source files must remain unchanged; the dangerous rule exists only in the temporary copy.
    original = (source / "HQ-R1.cfg").read_text(encoding="utf-8")
    assert permit not in original.split("ip access-list extended GUEST-IN", 1)[1].split("!", 1)[0]


def test_deployment_readiness_fails_closed_without_candidate_directory():
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"P3_ENABLE_DEPLOYMENT", "P3_CANDIDATE_DIR"}
    }
    env["P3_ENABLE_DEPLOYMENT"] = "YES_I_HAVE_A_DISPOSABLE_LAB"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_deployment_ready.py")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "P3_CANDIDATE_DIR must be set" in result.stderr


def test_deployment_readiness_rejects_default_unverified_inventory(tmp_path):
    marker = tmp_path / "DEPLOYMENT_READY"
    marker.write_text("I_RECONCILED_THIS_CANDIDATE_WITH_THE_LAB_BASELINE\n", encoding="utf-8")
    for name in ("HQ-R1", "BR1-R1", "BR2-R1", "HQ-SW1", "BR1-SW1", "BR2-SW1"):
        (tmp_path / f"{name}.cfg").write_text("! harmless test-only placeholder\n", encoding="utf-8")
    env = dict(os.environ)
    env["P3_ENABLE_DEPLOYMENT"] = "YES_I_HAVE_A_DISPOSABLE_LAB"
    env["P3_CANDIDATE_DIR"] = str(tmp_path.resolve())
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_deployment_ready.py")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "must explicitly set deployment_verified: true" in result.stderr


def test_pyats_testbed_builder_rejects_documentation_addresses():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_pyats_testbed.py"), "--output", str(ROOT / "build" / "unused-testbed.yml")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "documentation TEST-NET address" in result.stderr
