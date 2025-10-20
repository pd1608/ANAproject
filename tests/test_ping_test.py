import pytest
from unittest.mock import patch, MagicMock, mock_open
from pythonscripts import ping_test as pt

# -----------------------------
# Test: load_devices
# -----------------------------
@patch("builtins.open", new_callable=mock_open, read_data="Device,Hostname,Username,New_Password\n10.0.0.1,r1,admin,pass123\n")
def test_load_devices_success(mock_file):
    devices = pt.load_devices("dummy.csv")
    assert len(devices) == 1
    assert devices[0]["ip"] == "10.0.0.1"
    assert devices[0]["hostname"] == "r1"
    assert devices[0]["username"] == "admin"
    assert devices[0]["password"] == "pass123"

# -----------------------------
# Test: get_device_type
# -----------------------------
def test_get_device_type_cisco():
    assert pt.get_device_type("r1") == "cisco_ios"

def test_get_device_type_arista():
    assert pt.get_device_type("switch1") == "arista_eos"

# -----------------------------
# Test: run_ping_on_device
# -----------------------------
@patch("pythonscripts.ping_test.ConnectHandler")
def test_run_ping_success(mock_connect):
    mock_conn = MagicMock()
    mock_conn.find_prompt.return_value = "R1#"
    mock_conn.send_command.side_effect = [
        "Success rate is 100 percent",
        "Success rate is 100 percent",
        "0% packet loss"
    ]
    mock_connect.return_value = mock_conn

    device = {"ip": "10.0.0.1", "hostname": "r1", "username": "admin", "password": "pass123"}
    results = pt.run_ping_on_device(device)
    assert len(results) == 3
    for line in results:
        assert "✅ Success" in line

@patch("pythonscripts.ping_test.ConnectHandler")
def test_run_ping_failure(mock_connect):
    mock_conn = MagicMock()
    mock_conn.find_prompt.return_value = "R1#"
    mock_conn.send_command.side_effect = [
        "Success rate is 0 percent",
        "0% packet loss",
        "some error"
    ]
    mock_connect.return_value = mock_conn

    device = {"ip": "10.0.0.1", "hostname": "r1", "username": "admin", "password": "pass123"}
    results = pt.run_ping_on_device(device)
    assert any("❌ Failed" in line for line in results)

@patch("pythonscripts.ping_test.ConnectHandler", side_effect=Exception("SSH failed"))
def test_run_ping_connection_error(mock_connect):
    device = {"ip": "10.0.0.1", "hostname": "r1", "username": "admin", "password": "pass123"}
    results = pt.run_ping_on_device(device)
    assert len(results) == 1
    assert "Connection failed" in results[0]

def test_run_ping_skipped_device():
    device = {"ip": "10.0.0.1", "hostname": "switch1", "username": "admin", "password": "pass123"}
    results = pt.run_ping_on_device(device)
    assert results == []

# -----------------------------
# Test: main function
# -----------------------------
@patch("pythonscripts.ping_test.load_devices")
@patch("builtins.open", new_callable=mock_open)
@patch("pythonscripts.ping_test.run_ping_on_device")
def test_main(mock_ping, mock_file, mock_load_devices, capsys):
    mock_load_devices.return_value = [
        {"ip": "10.0.0.1", "hostname": "r1", "username": "admin", "password": "pass123"}
    ]
    mock_ping.return_value = ["r1 → 10.0.0.1: ✅ Success"]

    pt.main()
    captured = capsys.readouterr()
    assert "DEVICE PING TEST" in captured.out
    assert "r1 → 10.0.0.1: ✅ Success" in captured.out
    assert "Results saved to" in captured.out
