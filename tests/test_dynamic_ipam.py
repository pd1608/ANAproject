import pytest
from unittest.mock import patch, MagicMock, mock_open
from pythonscripts import dynamic_ipam as dia

# -----------------------------
# Test: read_device_passwords
# -----------------------------
@patch("builtins.open", new_callable=mock_open, read_data="Device,Hostname,Username,New_Password\n10.0.0.1,router1,admin,pass123\n")
def test_read_device_passwords(mock_file):
    devices = dia.read_device_passwords()
    assert len(devices) == 1
    device = devices[0]
    assert device["host"] == "10.0.0.1"
    assert device["hostname"] == "router1"
    assert device["username"] == "admin"
    assert device["password"] == "pass123"


# -----------------------------
# Test: collect_ipam
# -----------------------------
@patch("pythonscripts.dynamic_ipam.ConnectHandler")
@patch("builtins.open", new_callable=mock_open)
@patch("csv.writer")
@patch("pythonscripts.dynamic_ipam.read_device_passwords")
def test_collect_ipam_success(mock_read, mock_csv_writer, mock_file, mock_connect):
    # Mock device list
    mock_read.return_value = [
        {"host": "10.0.0.1", "hostname": "router1", "username": "admin", "password": "pass123"}
    ]

    # Mock Netmiko connection outputs
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = [
        # show ip interface brief (IPv4)
        "Interface IP-Address\nEthernet1 10.0.0.1\nEthernet2 unassigned",
        # show ipv6 interface brief
        "Interface IP-Address\nEthernet1 2001:db8::1\nEthernet2 unassigned",
        # show interfaces description | include Loopback
        "Loopback0\nLoopback1"
    ]
    mock_connect.return_value = mock_conn

    # Run the function
    dia.collect_ipam()

    # Verify ConnectHandler called correctly
    mock_connect.assert_called_once_with(
        device_type="arista_eos",
        host="10.0.0.1",
        username="admin",
        password="pass123"
    )

    # Verify CSV writer calls
    writer_instance = mock_csv_writer.return_value

    # Expected rows:
    # 1 header
    # 1 IPv4
    # 1 IPv6
    # 2 loopbacks
    expected_rows = [
        ["Hostname", "Device", "Interface", "IP Address", "IP Version"],
        ["router1", "10.0.0.1", "Ethernet1", "10.0.0.1", "IPv4"],
        ["router1", "10.0.0.1", "Ethernet1", "2001:db8::1", "IPv6"],
        ["router1", "10.0.0.1", "Loopback0", "Loopback", "N/A"],
        ["router1", "10.0.0.1", "Loopback1", "Loopback", "N/A"]
    ]

    # Check each call matches expected row
    for call, expected in zip(writer_instance.writerow.call_args_list, expected_rows):
        args, _ = call
        assert args[0] == expected


# -----------------------------
# Test: collect_ipam handles connection error
# -----------------------------
@patch("pythonscripts.dynamic_ipam.ConnectHandler", side_effect=Exception("SSH failed"))
@patch("pythonscripts.dynamic_ipam.read_device_passwords")
@patch("builtins.open", new_callable=mock_open)
def test_collect_ipam_connection_error(mock_file, mock_read, mock_connect):
    mock_read.return_value = [
        {"host": "10.0.0.1", "hostname": "router1", "username": "admin", "password": "pass123"}
    ]

    # Should print error but not raise
    dia.collect_ipam()
    mock_connect.assert_called_once()
