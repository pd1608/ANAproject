#!/usr/bin/env python3
import csv
import random
import string
from datetime import datetime
from netmiko import ConnectHandler
import time

PASSWORD_FILE = "/home/student/lab1/rotated_passwords.csv"
LOG_FILE = "/home/student/lab1/pythonscripts/password_rotation.log"


def generate_password(length=16):
    """Generate a secure random password with only alphabets and digits."""
    chars = string.ascii_letters + string.digits  # Exclude punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def log(message):
    """Write log messages with timestamps."""
    with open(LOG_FILE, "a") as logf:
        logf.write(f"[{datetime.now()}] {message}\n")
    print(message)


def read_device_passwords():
    """Read current device passwords from CSV."""
    devices = []
    with open(PASSWORD_FILE, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            devices.append({
                "Device": row["Device"].strip(),
                "Username": row["Username"].strip(),
                "Old_Password": row["New_Password"].strip()
            })
    return devices


def write_new_passwords(devices):
    """Overwrite CSV file with newly rotated passwords including Hostname."""
    with open(PASSWORD_FILE, mode="w", newline="") as csvfile:
        fieldnames = ["Device", "Hostname", "Username", "New_Password"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for dev in devices:
            writer.writerow({
                "Device": dev["Device"],
                "Hostname": dev.get("Hostname", "N/A"),
                "Username": dev["Username"],
                "New_Password": dev["New_Password"]
            })


def rotate_passwords():
    devices = read_device_passwords()
    updated_devices = []

    for dev in devices:
        new_password = generate_password()
        device = {
            "device_type": "arista_eos",
            "host": dev["Device"],
            "username": dev["Username"],
            "password": dev["Old_Password"],
            "fast_cli": False,
            "global_delay_factor": 2,
            "read_timeout_override": 60,
            "session_log": f"session_{dev['Device']}.log"
        }

        log(f"\n[+] Connecting to {dev['Device']}...")

        try:
            conn = ConnectHandler(**device)
            conn.enable()

            # Capture hostname (strip '#' or '>')
            prompt = conn.find_prompt()
            hostname = prompt.replace("#", "").replace(">", "").strip()
            dev["Hostname"] = hostname

            # Rotate password
            commands = [f"username {dev['Username']} secret {new_password}"]
            conn.send_config_set(commands)
            conn.save_config()
            conn.disconnect()

            log(f"[+] Password successfully rotated for {dev['Device']} ({hostname})")
            dev["New_Password"] = new_password
            updated_devices.append(dev)

        except Exception as e:
            log(f"[-] Failed to update {dev['Device']}: {e}")
            dev["New_Password"] = dev["Old_Password"]
            dev["Hostname"] = "N/A"
            updated_devices.append(dev)

        # Small delay to prevent overloading
        time.sleep(2)

    # Write new passwords with hostname column
    write_new_passwords(updated_devices)
    log("\n✅ Password rotation completed successfully!\n")


if __name__ == "__main__":
    rotate_passwords()
