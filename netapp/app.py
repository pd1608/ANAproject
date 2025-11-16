from flask import Flask, render_template, request, redirect, url_for, flash
from jinja2 import Environment, FileSystemLoader
from napalm import get_network_driver
import os
from datetime import datetime
import subprocess
import sys
import csv
from flask import send_file
import difflib
import time
import requests # New import for Jenkins integration


app = Flask(__name__)
app.secret_key = 'supersecretkey' # Needed for flash messages

# Path to your Jinja2 templates
TEMPLATE_DIR = 'templates/' # Put your .j2 files here
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Dummy list of templates to populate dropdown
templates = [
    ('access_router.j2', 'Access Router'),
    ('access_switch.j2', 'Access Switch'),
    ('core_router.j2', 'Core Router'),
    ('core_switch.j2', 'Core Switch')
]

# --- Global Configurations ---
ROTATED_PASSWORD_FILE = "/home/student/lab1/rotated_passwords.csv"
GOLDEN_CONFIG_FOLDER = "/home/student/lab1/pythonscripts/golden_configs/"
IPAM_CSV = "/home/student/lab1/pythonscripts/dynamic_ipam.csv" # Path to your IPAM CSV

# Jenkins Configuration (ADDED/MODIFIED)
JENKINS_USER = "admin"
JENKINS_TOKEN = "11078f29dad7d537dbe9be9cf51f68e962"
# CORRECTED: Must use buildWithParameters for parameterized jobs
JENKINS_JOB_URL = "http://127.0.0.1:8080/job/Add_device_ANA/buildWithParameters"
JENKINS_TRIGGER_TOKEN = "Add_device"


def load_devices_from_csv():
    """Load devices from CSV using column positions (0=IP, 1=Hostname, 2=Username, 3=Password)"""
    devices_list = []
    try:
        with open(ROTATED_PASSWORD_FILE, "r") as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                # strip spaces just in case
                ip = row[0].strip()
                hostname = row[1].strip()
                username = row[2].strip()
                password = row[3].strip()
                devices_list.append({
                    "device_ip": ip,
                    "device_name": hostname,
                    "username": username,
                    "password": password
                })
    except FileNotFoundError:
        print(f"❌ Rotated password CSV not found at {ROTATED_PASSWORD_FILE}")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
    return devices_list

# Load devices once at startup
devices = load_devices_from_csv()


@app.route('/')
def index():
    return render_template('index.html', templates=templates, devices=devices)

@app.route('/add', methods=['POST'])
def add_device():
    global devices # MUST declare global to update the module-level variable
    try:
        form = request.form.to_dict()

        # --- Step 0: Collect interfaces dynamically ---
        interfaces = []
        index = 0
        while f'interface_name_{index}' in form:
            iface = {
                'name': form.get(f'interface_name_{index}'),
                'ip': form.get(f'interface_ip_{index}'),
                'mask': form.get(f'interface_mask_{index}'),
                'ipv6': form.get(f'interface_ipv6_{index}'),
                'shutdown': f'interface_shutdown_{index}' in form
            }
            interfaces.append(iface)
            index += 1

        # --- Step 1: Prepare variables for Jinja2 ---
        template_vars = {
            'device_name': form.get('device_name'),
            'hostname': form.get('hostname'),
            'vendor': form.get('vendor'),
            'interfaces': interfaces,
            'ospf_process': form.get('ospf_process'),
            'ospf_max_lsa': form.get('ospf_max_lsa'),
            'rip_networks': request.form.getlist('rip_network'),
            'bgp_asn': form.get('bgp_asn'),
            'bgp_neighbors': [
                {'ip': form.get(f'bgp_neighbor_ip_{i}'), 'asn': form.get(f'bgp_neighbor_as_{i}')}
                for i in range(len([k for k in form.keys() if k.startswith('bgp_neighbor_ip_')]))
            ],
            'default_gateway': form.get('default_gateway'),
            'default_gateway_v6': form.get('default_gateway_v6'),
            'vlans': [
                {'id': form.get('vlan_id_0'), 'name': form.get('vlan_name_0')}
            ] if form.get('vlan_id_0') else []
        }

        # --- Step 2: Render Jinja2 config ---
        template_name = form.get('j2_template')
        template = env.get_template(template_name)
        rendered_config = template.render(template_vars)

        # --- Step 3: ZTP Automation (DHCP/Ping) ---
        management_ip = form.get('management_ip')
        mac_address = form.get('mac_address')
        
        dhcp_server_ip = "10.0.100.6"
        dhcp_device = next((d for d in devices if d["device_ip"] == dhcp_server_ip), None)
        if not dhcp_device:
            flash(f"DHCP server {dhcp_server_ip} not found in CSV", "error")
            return render_template('rendered_config.html', config=rendered_config)

        # 3a: Connect to DHCP server and create reservation
        driver = get_network_driver("eos")
        optional_args = {"transport": "ssh"}
        with driver(
            hostname=dhcp_device["device_ip"],
            username=dhcp_device["username"],
            password=dhcp_device["password"],
            optional_args=optional_args
        ) as dhcp_conn:
            dhcp_cmds = [
                "configure terminal",
                "dhcp server",
                "   subnet 10.0.100.0/24",
                "      reservations",
                f"         mac-address {mac_address}",
                f"            ipv4-address {management_ip}",
                "end",
                "write memory"
            ]
            dhcp_conn.load_merge_candidate(config=dhcp_cmds)
            dhcp_conn.commit_config()

        flash(f"✅ DHCP reservation created for {management_ip} ({mac_address})", "success")

        # 3b: Wait and ping device
        time.sleep(10)
        ping_result = subprocess.run(
            ["ping", "-c", "3", management_ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if "0% packet loss" not in ping_result.stdout:
            flash(f"⚠ Device {management_ip} not reachable via ping. ZTP halted.", "error")
            return render_template('rendered_config.html', config=rendered_config)

        flash(f"✅ Device {management_ip} is reachable via ping", "success")

        # --- Step 3c: Update rotated_passwords.csv (IMPROVED) ---
        try:
            with open(ROTATED_PASSWORD_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                # Write the new device entry with default 'admin' credentials
                writer.writerow([management_ip, template_vars['hostname'], "admin", "admin"])
            
            # Reload global devices list from file to reflect the change
            devices = load_devices_from_csv()
            flash(f"✅ Added {management_ip} to rotated passwords file and reloaded device list", "success")
        except Exception as e:
            flash(f"❌ Failed to update rotated passwords CSV: {e}", "error")


        # --- Step 4: Trigger Jenkins Pipeline (FIXED) ---

        # Prepare parameters for the Jenkins job, including the token
        params = {
            "token": JENKINS_TRIGGER_TOKEN, # The Jenkins remote build token
            "DEVICE_IP": management_ip,
            "HOSTNAME": template_vars['hostname'],
            "TEMPLATE": template_name
        }

        try:
            response = requests.post(
                JENKINS_JOB_URL, # Uses /buildWithParameters
                auth=(JENKINS_USER, JENKINS_TOKEN),
                params=params
            )
            
            # 200/201 indicates a successful trigger
            if response.status_code in [200, 201]: 
                flash(f"✅ Jenkins Pipeline triggered successfully for {management_ip}", "success")
            else:
                flash(f"❌ Failed to trigger Jenkins Pipeline: HTTP {response.status_code}. Check URL, Token, and API Key.", "error")
        except Exception as e:
            flash(f"❌ Error triggering Jenkins Pipeline: {e}", "error")

        return render_template('rendered_config.html', config=rendered_config)

    except Exception as e:
        flash(f"Error in add_device process: {e}", "error")
        return render_template('rendered_config.html', config=rendered_config)


# GOLDEN_CONFIG_FOLDER is already defined globally
GOLDEN_CONFIG_FOLDER = "/home/student/lab1/pythonscripts/netapp/golden_configs" # NOTE: Duplicates definition above, kept for consistency

@app.route("/golden_config", methods=["POST"])
def create_golden_config():
    device_input = request.form.get("hostname", "").strip()

    # Lookup device by IP or name
    device = next(
        (d for d in devices if d["device_ip"] == device_input or d["device_name"].lower() == device_input.lower()),
        None
    )

    if not device:
        flash(f"Device '{device_input}' not found!", "error")
        return redirect(url_for("index"))

    try:
        # NAPALM driver for Arista EOS via SSH
        driver = get_network_driver("eos")
        optional_args = {"transport": "ssh"}
        with driver(
            hostname=device["device_ip"],
            username=device["username"],
            password=device["password"],
            optional_args=optional_args
        ) as device_conn:
            running_config = device_conn.get_config()["running"]

        # Ensure the folder exists
        os.makedirs(GOLDEN_CONFIG_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{device['device_name']}_golden_{timestamp}.cfg"
        filepath = os.path.join(GOLDEN_CONFIG_FOLDER, filename)

        with open(filepath, "w") as f:
            f.write(running_config)

        flash(f"Golden config saved: {filename}", "success")
        return send_file(filepath, as_attachment=True)

    except Exception as e:
        flash(f"Failed to create golden config: {str(e)}", "error")
        return redirect(url_for("index"))



@app.route("/config_diff", methods=["POST"])
def config_diff():
    import difflib

    device_input = request.form.get("hostname", "").strip().lower()

    # Find latest golden config for device
    golden_files = [
        f for f in os.listdir(GOLDEN_CONFIG_FOLDER)
        if f.lower().startswith(device_input)
    ]
    if not golden_files:
        flash(f"No golden config found for device '{device_input}'", "error")
        return redirect(url_for("index"))

    latest_file = sorted(golden_files, reverse=True)[0]
    golden_filepath = os.path.join(GOLDEN_CONFIG_FOLDER, latest_file)

    with open(golden_filepath, "r") as f:
        golden_config = [line.strip() for line in f if line.strip() and not line.strip().startswith(("!", "#"))]

    # Find device credentials
    device = next(
        (d for d in devices if d["device_name"].lower().startswith(device_input)),
        None
    )
    if not device:
        flash(f"Device '{device_input}' not found in devices list", "error")
        return redirect(url_for("index"))

    try:
        driver = get_network_driver("eos") # SSH connection
        optional_args = {"transport": "ssh"}
        with driver(
            hostname=device["device_ip"],
            username=device["username"],
            password=device["password"],
            optional_args=optional_args
        ) as device_conn:
            running_config = [
                line.strip() for line in device_conn.get_config()["running"].splitlines()
                if line.strip() and not line.strip().startswith(("!", "#"))
            ]

        # Minimalist diff: only lines that differ
        diff_lines = []
        for line in difflib.ndiff(golden_config, running_config):
            if line.startswith("- ") or line.startswith("+ "):
                diff_lines.append(line)

        if not diff_lines:
            diff_output = "✅ No differences! Running config matches the golden config."
        else:
            diff_output = "\n".join(diff_lines)

        return render_template("config_diff.html", hostname=device_input.upper(), diff=diff_output)

    except Exception as e:
        flash(f"Failed to fetch running config or generate diff: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/health_check", methods=["POST"])
def health_check():
    hostname = request.form.get("hostname")

    result = subprocess.run(
        [sys.executable, "/home/student/lab1/pythonscripts/device_health_check.py", hostname],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    output = result.stdout + "\n" + result.stderr
    return render_template("health_output.html", hostname=hostname, output=output)

# IPAM_CSV is already defined globally

@app.route("/ipam_view", methods=["GET"])
def ipam_view():
    ipam_data = []

    try:
        with open(IPAM_CSV, mode="r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ipam_data.append(row)
    except FileNotFoundError:
        flash(f"IPAM CSV not found at {IPAM_CSV}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error reading IPAM CSV: {e}", "error")
        return redirect(url_for("index"))

    return render_template("ipam_full.html", ipam_data=ipam_data)

@app.route("/show_running_config", methods=["POST"])
def show_running_config():
    import csv
    from netmiko import ConnectHandler

    device_ip = request.form.get("device_ip")

    # Read credentials from CSV
    username = None
    password = None
    with open("/home/student/lab1/rotated_passwords.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get("Device") == device_ip or row.get("Hostname").lower() == device_ip.lower():
                username = row.get("Username")
                password = row.get("New_Password")
                break

    if not username or not password:
        return render_template("running_config.html",
                               device_ip=device_ip,
                               output=f"❌ No credentials found in rotated_passwords.csv for {device_ip}")

    # SSH and fetch running config
    try:
        device = {
            "device_type": "arista_eos",  # adjust as needed, e.g., "arista_eos"
            "ip": device_ip,
            "username": username,
            "password": password,
        }

        net_connect = ConnectHandler(**device)
        net_connect.enable()
        output = net_connect.send_command("show running-config")
        net_connect.disconnect()

        return render_template("running_config.html",
                               device_ip=device_ip,
                               output=output)

    except Exception as e:
        return render_template("running_config.html",
                               device_ip=device_ip,
                               output=f"❌ SSH error: {str(e)}")




if __name__ == '__main__':
    app.run(debug=True)