import pytest
import builtins
from unittest.mock import patch, MagicMock
from pythonscripts import check_cpu
import subprocess


# ---- TEST: Successful CPU usage retrieval ----
@patch("subprocess.check_output")
def test_get_cpu_usage_success(mock_subprocess):
    mock_subprocess.return_value = b"""
    HOST-RESOURCES-MIB::hrProcessorLoad.1 = INTEGER: 30
    HOST-RESOURCES-MIB::hrProcessorLoad.2 = INTEGER: 50
    HOST-RESOURCES-MIB::hrProcessorLoad.3 = INTEGER: 40
    """

    result = check_cpu.get_cpu_usage("10.0.100.2", "public")
    # Expect average = (30 + 50 + 40) / 3 = 40.0
    assert result == pytest.approx(40.0)


# ---- TEST: Empty SNMP output ----
@patch("subprocess.check_output")
def test_get_cpu_usage_empty_output(mock_subprocess):
    mock_subprocess.return_value = b""
    result = check_cpu.get_cpu_usage("10.0.100.3", "public")
    assert result is None


# ---- TEST: Subprocess failure ----
@patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "snmpwalk"))
def test_get_cpu_usage_exception(mock_subprocess):
    result = check_cpu.get_cpu_usage("10.0.100.4", "public")
    assert result is None


# ---- TEST: Main function output with high CPU ----
@patch("pythonscripts.check_cpu.get_cpu_usage", return_value=80)
def test_main_high_cpu(mock_cpu, capsys):
    check_cpu.THRESHOLD = 50
    check_cpu.DEVICES = [{"ip": "10.0.100.2", "community": "public"}]

    check_cpu.main()
    captured = capsys.readouterr()
    assert "ALERT: CPU usage" in captured.out
    assert "10.0.100.2" in captured.out


# ---- TEST: Main function output with normal CPU ----
@patch("pythonscripts.check_cpu.get_cpu_usage", return_value=30)
def test_main_normal_cpu(mock_cpu, capsys):
    check_cpu.THRESHOLD = 50
    check_cpu.DEVICES = [{"ip": "10.0.100.3", "community": "public"}]

    check_cpu.main()
    captured = capsys.readouterr()
    assert "ALERT" not in captured.out


# ---- TEST: Main function output when SNMP fails ----
@patch("pythonscripts.check_cpu.get_cpu_usage", return_value=None)
def test_main_snmp_failure(mock_cpu, capsys):
    check_cpu.DEVICES = [{"ip": "10.0.100.4", "community": "public"}]

    check_cpu.main()
    captured = capsys.readouterr()
    assert "ERROR: Unable to fetch CPU usage" in captured.out
