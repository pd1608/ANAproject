#!/usr/bin/env python3
import argparse
import csv
import sys
import time
from netmiko import ConnectHandler

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
# Fallback user (used only if CSV does not supply a username)
FALLBACK_USERNAME = "admin"
DEVICE_TYPE = "arista_eos"  # Change to match your platform (e.g., juniper, linux, etc.)

# Test parameters
PING_IPV4 = "198.100.100.2"
PING_IPV6 = "2003:db8::1"

# Path to rotated passwords CSV (must contain Device, Hostname, Username, New_Password)
PASSWORD_FILE = "/home/student/lab1/rotated_passwords.csv"


# ------------------------------------------------------------
# CSV helper
# ------------------------------------------------------------
def find_credentials(target):
    """
    Find credentials for a target identifier (hostname or device IP) in the CSV.
    Matching is case-insensitive against both Device and Hostname columns.
    Returns a tuple (username, password) or (None, None) if not found.
    """
    target_norm = (target or "").strip().lower()
    try:
        with open(PASSWORD_FILE, mode="r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                device_val = row.get("Device", "").strip().lower()
                hostname_val = row.get("Hostname", "").strip().lower()
                if target_norm == device_val or (hostname_val and target_norm == hostname_val):
                    username = row.get("Username", "").strip() or FALLBACK_USERNAME
                    password = row.get("New_Password", "").strip()
                    return username, password
    except FileNotFoundError:
        print(f"❌ Password file not found: {PASSWORD_FILE}")
    except Exception as e:
        print(f"❌ Error reading password file: {e}")

    return None, None


# ------------------------------------------------------------
# Functions
# ------------------------------------------------------------
def check_ping(connection):
    """Ping test for IPv4 and IPv6"""
    print("\n[+] Testing connectivity...")
    ipv4_result = connection.send_command(f"ping {PING_IPV4}")
    ipv6_result = connection.send_command(f"ping ipv6 {PING_IPV6}")

    print(f"IPv4 Ping Result:\n{ipv4_result}\n")
    print(f"IPv6 Ping Result:\n{ipv6_result}\n")

    if "Success rate is 0 percent" in ipv4_result or "Success rate is 0 percent" in ipv6_result:
        print("❌ Ping test failed")
    else:
        print("✅ Ping test successful")


def show_routes_and_neighbors(connection):
    """Display routing table and neighbor relationships"""
    print("\n[+] Retrieving routing table and neighbor information...")
    routes = connection.send_command("show ip route")
    # Try structured output for OSPF neighbors, fallback to CDP/LLDP if empty
    try:
        neighbors = connection.send_command("show ip ospf neighbor", use_textfsm=True)
    except Exception:
        neighbors = None

    if not neighbors:
        # Try CDP, then LLDP
        neighbors = connection.send_command("show cdp neighbors") or connection.send_command("show lldp neighbors")

    print("\n=== Routing Table ===")
    print(routes)
    print("\n=== Neighbors ===")
    print(neighbors if neighbors else "No neighbor data found.")


def check_cpu_utilization(connection):
    """Check CPU utilization on Arista EOS and ensure it's below 70%."""
    print("\n[+] Checking CPU utilization...")

    try:
        # Enter privileged EXEC mode
        connection.enable()

        # Run bash command to get CPU usage (%user + %system + %nice)
        cpu_output = connection.send_command(
            'bash top -b -n1 | grep "Cpu(s)" | awk \'{print $2 + $4 + $6}\''
        )

        print(f"Raw CPU Output: {cpu_output.strip()}")

        # Clean and convert output to float
        cpu_value = float(cpu_output.strip())

        # Evaluate CPU threshold
        if cpu_value < 70:
            print(f"✅ CPU utilization OK ({cpu_value:.2f}%)")
        else:
            print(f"⚠️ CPU utilization high ({cpu_value:.2f}%)")

    except ValueError:
        print(f"⚠️ Unable to parse CPU utilization value: '{cpu_output.strip()}'")
    except Exception as e:
        print(f"⚠️ Error while checking CPU utilization: {e}")


# ------------------------------------------------------------
# Main logic
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Device Health Check Script (uses rotated_passwords.csv for auth)")
    parser.add_argument(
        "hostname",
        help="Hostname or IP address of the device to test (will be matched against Device or Hostname fields in CSV)"
    )
    args = parser.parse_args()

    # Look up username/password from CSV
    username, password = find_credentials(args.hostname)
    if username is None or password is None:
        print(f"❌ No credentials found in {PASSWORD_FILE} for '{args.hostname}'.")
        print("Please ensure rotated_passwords.csv contains a matching 'Device' or 'Hostname' entry with 'Username' and 'New_Password'.")
        sys.exit(1)

    device = {
        "device_type": DEVICE_TYPE,
        "host": args.hostname,
        "username": username,
        "password": password,
        "fast_cli": False,
    }

    try:
        print(f"Connecting to {args.hostname} (user: {username})...")
        connection = ConnectHandler(**device)
        print(f"✅ Connected to {args.hostname}\n")

        check_ping(connection)
        show_routes_and_neighbors(connection)
        check_cpu_utilization(connection)

        connection.disconnect()
        print(f"\n✅ All tests completed for {args.hostname}")
    except Exception as e:
        print(f"❌ Connection or test failed for {args.hostname}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
