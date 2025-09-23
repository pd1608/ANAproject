from napalm import get_network_driver
import yaml
import os

def get_running_config(host, username, password):
    # Load EOS driver
    driver = get_network_driver("eos")

    # Connect to device
    device = driver(hostname=host, username=username, password=password, optional_args={})
    device.open()

    # Get running config
    config = device.get_config()["running"]

    device.close()
    return config

if __name__ == "__main__":
    # List of devices (hostname: IP)
    devices = {
        "s1": "10.0.100.8",
        "r1": "10.0.100.9",
        "s3": "10.0.100.2",
        "r3": "10.0.100.3"
    }

    username = "admin"
    password = "pranav"

    # Output directory
    output_dir = "/home/student/lab1/pythonscripts/templateyaml"
    os.makedirs(output_dir, exist_ok=True)  # create dir if not exists

    for name, ip in devices.items():
        print(f"📡 Fetching running config from {name} ({ip})...")

        config = get_running_config(ip, username, password)

        # Split config into lines and store as list
        config_lines = config.splitlines()

        # Save to YAML file (per device) inside the target folder
        filename = os.path.join(output_dir, f"{name}-running-config.yaml")
        with open(filename, "w") as f:
            yaml.dump(config_lines, f, default_flow_style=False)

        print(f"✅ Running config for {name} saved to {filename}")

