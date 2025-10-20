#!/usr/bin/env python3
import csv
from netmiko import ConnectHandler
from datetime import datetime

CSV_FILE = "/home/student/lab1/rotated_passwords.csv"
LOG_FILE = "/home/student/lab1/pythonscripts/ping_results.txt"

PING_TARGETS = [
    "198.100.100.2",
    "2003:db8::1",
    "10.0.100.1"
]

def load_devices(csv_file):
    """Load device details from CSV"""
    devices = []
    with open(csv_file, mode="r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            devices.append({
                "ip": row["Device"].strip(),
                "hostname": row["Hostname"].strip(),
                "username": row["Username"].strip(),
                "password": row["New_Password"].strip()
            })
    return devices

def get_device_type(hostname):
    """Infer device type from hostname"""
    if hostname.startswith("r"):
        return "cisco_ios"
    return "arista_eos"

def run_ping_on_device(device):
    """SSH into device and run ping commands"""
    hostname = device["hostname"]

    # Skip devices not starting with 'r'
    if not hostname.lower().startswith("r"):
        return []

    ip = device["ip"]
    username = device["username"]
    password = device["password"]

    print(f"\n🔹 Connecting to {hostname} ({ip}) ...")

    device_type = get_device_type(hostname)
    device_params = {
        "device_type": device_type,
        "host": ip,
        "username": username,
        "password": password,
        "fast_cli": False
    }

    results = []
    try:
        conn = ConnectHandler(**device_params)
        conn.find_prompt()  # Verify connection

        for target in PING_TARGETS:
            print(f"  🔸 Pinging {target} from {hostname} ...")

            if ":" in target:
                ping_cmd = f"ping ipv6 {target}" if device_type != "arista_eos" else f"ping ipv6 {target} repeat 3"
            else:
                ping_cmd = f"ping {target}" if device_type != "arista_eos" else f"ping {target} repeat 3"

            output = conn.send_command(ping_cmd, expect_string=None, delay_factor=2)

            success = any(kw in output.lower() for kw in ["success rate", "bytes from", "100 percent", "0% packet loss"])
            status = "✅ Success" if success else "❌ Failed"
            results.append(f"{hostname} → {target}: {status}")

        conn.disconnect()

    except Exception as e:
        results.append(f"❌ Connection failed for {hostname} ({ip}): {str(e)}")

    return results

def main():
    devices = load_devices(CSV_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n===== DEVICE PING TEST ({timestamp}) =====\n")
    with open(LOG_FILE, "w") as log:
        log.write(f"===== DEVICE PING TEST ({timestamp}) =====\n\n")

        for device in devices:
            results = run_ping_on_device(device)
            for line in results:
                print(line)
                log.write(line + "\n")

    print(f"\n✅ Results saved to {LOG_FILE}\n")

if __name__ == "__main__":
    main()
