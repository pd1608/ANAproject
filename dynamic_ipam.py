#!/usr/bin/env python3
import csv
from netmiko import ConnectHandler

# Input file containing rotated passwords with Hostname column
PASSWORD_FILE = "/home/student/lab1/rotated_passwords.csv"

# Output CSV file for IPAM data
OUTPUT_FILE = "dynamic_ipam.csv"


def read_device_passwords():
    """Read device details and passwords (including Hostname) from rotated_passwords.csv"""
    devices = []
    with open(PASSWORD_FILE, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            devices.append({
                "host": row["Device"].strip(),
                "hostname": row.get("Hostname", "N/A").strip(),
                "username": row["Username"].strip(),
                "password": row["New_Password"].strip()
            })
    return devices


def collect_ipam():
    """SSH into each device and collect IP address information."""
    devices = read_device_passwords()

    with open(OUTPUT_FILE, mode="w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Hostname", "Device", "Interface", "IP Address", "IP Version"])

        for dev in devices:
            device = {
                "device_type": "arista_eos",  # Adjust as needed
                "host": dev["host"],
                "username": dev["username"],
                "password": dev["password"],
            }

            print(f"🔗 Connecting to {dev['hostname']} ({dev['host']})...")
            try:
                connection = ConnectHandler(**device)

                # --- IPv4 addresses ---
                ipv4_output = connection.send_command("show ip interface brief")
                lines = ipv4_output.splitlines()
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        interface = parts[0]
                        ip_address = parts[1]
                        if ip_address.lower() != "unassigned":
                            csv_writer.writerow([dev["hostname"], dev["host"], interface, ip_address, "IPv4"])

                # --- IPv6 addresses ---
                ipv6_output = connection.send_command("show ipv6 interface brief")
                lines = ipv6_output.splitlines()
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        interface = parts[0]
                        ip_address = parts[1]
                        if ip_address.lower() != "unassigned":
                            csv_writer.writerow([dev["hostname"], dev["host"], interface, ip_address, "IPv6"])

                # --- Optional: capture Loopback interfaces ---
                loop_output = connection.send_command("show interfaces description | include Loopback")
                for line in loop_output.splitlines():
                    parts = line.split()
                    if parts:
                        interface = parts[0]
                        csv_writer.writerow([dev["hostname"], dev["host"], interface, "Loopback", "N/A"])

                connection.disconnect()
                print(f"✅ Finished collecting IPs for {dev['hostname']} ({dev['host']})")

            except Exception as e:
                print(f"❌ Failed to connect to {dev['hostname']} ({dev['host']}): {e}")

    print(f"\n📄 IPAM data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    collect_ipam()
