# tests/test_device_health_check.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
import builtins
import sys
import argparse

# Import the script as a module
from pythonscripts import device_health_check as dhc


# ------------------------------
# Test: find_credentials
# ------------------------------
@patch("builtins.open", new_callable=mock_open, read_data="Device,Hostname,Username,New_Password\nrouter1,router1,admin,pass123\n")
def test_find_credentials_success(mock_file):
    username, password = dhc.find_credentials("router1")
    assert username == "admin"
    assert password == "pass123"

@patch("builtins.open", new_callable=mock_open)
def test_find_credentials_not_found(mock_file):
    username, password = dhc.find_credentials("unknown_device")
    assert username is None
    assert password is None

@patch("builtins.open", side_effect=FileNotFoundError)
def test_find_credentials_file_not_found(mock_file):
    username, password = dhc.find_credentials("router1")
    assert username is None
    assert password is None


# ------------------------------
# Test: check_ping
# ------------------------------
def test_check_ping_success(capsys):
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = [
        "Success rate is 100 percent",  # IPv4
        "Success rate is 100 percent",  # IPv6
    ]

    dhc.check_ping(mock_conn)
    captured = capsys.readouterr()
    assert "Ping test successful" in captured.out

def test_check_ping_failure(capsys):
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = [
        "Success rate is 0 percent",  # IPv4
        "Success rate is 100 percent",  # IPv6
    ]

    dhc.check_ping(mock_conn)
    captured = capsys.readouterr()
    assert "Ping test failed" in captured.out


# ------------------------------
# Test: show_routes_and_neighbors
# ------------------------------
def test_show_routes_and_neighbors_with_ospf(capsys):
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = [
        "routing table output",  # show ip route
        [{"neighbor": "R2"}],    # show ip ospf neighbor
    ]

    dhc.show_routes_and_neighbors(mock_conn)
    captured = capsys.readouterr()
    assert "Routing Table" in captured.out
    assert "neighbor" in captured.out

def test_show_routes_and_neighbors_fallback(capsys):
    mock_conn = MagicMock()
    # OSPF fails → fallback to CDP/LLDP
    mock_conn.send_command.side_effect = [
        "routing table output",  # show ip route
        Exception("OSPF failed"),  # show ip ospf neighbor
        "cdp neighbors output",  # fallback
        None,                    # fallback LLDP
    ]

    dhc.show_routes_and_neighbors(mock_conn)
    captured = capsys.readouterr()
    assert "Routing Table" in captured.out
    assert "cdp neighbors output" in captured.out


# ------------------------------
# Test: check_cpu_utilization
# ------------------------------
def test_check_cpu_utilization_ok(capsys):
    mock_conn = MagicMock()
    mock_conn.enable = MagicMock()
    mock_conn.send_command.return_value = "55.0"

    dhc.check_cpu_utilization(mock_conn)
    captured = capsys.readouterr()
    assert "CPU utilization OK" in captured.out

def test_check_cpu_utilization_high(capsys):
    mock_conn = MagicMock()
    mock_conn.enable = MagicMock()
    mock_conn.send_command.return_value = "80.0"

    dhc.check_cpu_utilization(mock_conn)
    captured = capsys.readouterr()
    assert "CPU utilization high" in captured.out

def test_check_cpu_utilization_parse_error(capsys):
    mock_conn = MagicMock()
    mock_conn.enable = MagicMock()
    mock_conn.send_command.return_value = "invalid_output"

    dhc.check_cpu_utilization(mock_conn)
    captured = capsys.readouterr()
    assert "Unable to parse CPU utilization value" in captured.out


# ------------------------------
# Test: main function
# ------------------------------
@patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(hostname="router1"))
@patch("builtins.open", new_callable=mock_open, read_data="Device,Hostname,Username,New_Password\nrouter1,router1,admin,pass123\n")
@patch("pythonscripts.device_health_check.ConnectHandler")
def test_main_success(mock_connect, mock_file, mock_args, capsys):
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "Success rate is 100 percent"
    mock_conn.enable = MagicMock()
    mock_connect.return_value = mock_conn

    # Run main
    with patch.object(sys, "exit") as mock_exit:
        dhc.main()
        captured = capsys.readouterr()
        assert "All tests completed" in captured.out
        mock_exit.assert_not_called()

@patch("argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(hostname="unknown"))
@patch("builtins.open", new_callable=mock_open, read_data="Device,Hostname,Username,New_Password\n")
def test_main_no_credentials(mock_file, mock_args, capsys):
    with patch.object(sys, "exit") as mock_exit:
        dhc.main()
        captured = capsys.readouterr()
        assert "No credentials found" in captured.out
        mock_exit.assert_called_once_with(1)
