import yaml
import csv
from pathlib import Path

CSV_FILE = "/home/student/lab1/rotated_passwords.csv"
YAML_FILE = "/home/student/lab1/pythonscripts/grpcclient.yaml"

def load_csv():
    devices = {}
    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ip = row["Device"].strip()
            hostname = row["Hostname"].strip()
            username = row["Username"].strip()
            password = row["New_Password"].strip()

            devices[hostname] = {
                "ip": ip,
                "username": username,
                "password": password,
            }
    return devices

def update_yaml(devices):
    # Load existing YAML or create new structure
    if Path(YAML_FILE).exists():
        with open(YAML_FILE) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    config["insecure"] = True
    config["username"] = "admin"
    config["password"] = "DO_NOT_USE"

    config.setdefault("targets", {})

    # Sync devices into YAML
    for hostname, info in devices.items():
        config["targets"][hostname] = {
            "address": f"{info['ip']}:6030",
            "username": info["username"],
            "password": info["password"],
        }

    # Save back to YAML
    with open(YAML_FILE, "w") as f:
        yaml.dump(config, f, sort_keys=False)

    print(f"✅ Synced grpcclient.yaml — {len(devices)} devices updated.")

def main():
    devices = load_csv()
    update_yaml(devices)

if __name__ == "__main__":
    main()
