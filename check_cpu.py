#!/usr/bin/env python3
import subprocess
import statistics
import sys
from datetime import datetime

# Config
DEVICES = [
    {"ip": "10.0.100.2", "community": "public"},
    {"ip": "10.0.100.3", "community": "public"},
    {"ip": "10.0.100.4", "community": "public"},
    {"ip": "10.0.100.5", "community": "public"},
    {"ip": "10.0.100.6", "community": "public"},
    {"ip": "10.0.100.7", "community": "public"},
    {"ip": "10.0.100.8", "community": "public"},
    {"ip": "10.0.100.9", "community": "public"}
]
THRESHOLD = 50  # CPU threshold in %

# OID for CPU usage per core
CPU_OID = ".1.3.6.1.2.1.25.3.3.1.2"

def get_cpu_usage(ip, community):
    """Run snmpwalk and return average CPU usage."""
    try:
        result = subprocess.check_output(
            ["snmpwalk", "-v2c", "-c", community, ip, CPU_OID],
            stderr=subprocess.DEVNULL
        ).decode()

        if not result.strip():
            return None

        # Extract CPU values (last column of each line)
        values = [int(line.split()[-1]) for line in result.strip().split("\n")]
        return statistics.mean(values)

    except subprocess.CalledProcessError:
        return None

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for device in DEVICES:
        ip = device["ip"]
        community = device["community"]

        avg_cpu = get_cpu_usage(ip, community)

        if avg_cpu is None:
            print(f"[{now}] ERROR: Unable to fetch CPU usage from {ip}")
            continue

        if avg_cpu > THRESHOLD:
            print(f"[{now}] ALERT: CPU usage on {ip} is HIGH ({avg_cpu:.2f}% > {THRESHOLD}%)")

if __name__ == "__main__":
    main()

