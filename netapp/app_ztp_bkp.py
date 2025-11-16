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
from netmiko import ConnectHandler  # <-- Added netmiko for SSH automation
import urllib.parse  # For encoding the bootstrap URL

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Path to your Jinja2 templates
TEMPLATE_DIR = 'templates/'  # Put your .j2 files here
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Dummy list of templates to populate dropdown
templates = [
    ('access_router.j2', 'Access Router'),
    ('access_switch.j2', 'Access Switch'),
    ('core_router.j2', 'Core Router'),
    ('core_switch.j2', 'Core Switch')
]

# ==============================================================================
# ZTP/DHCP CONFIGURATION CONSTANTS AND HELPER FUNCTIONS
# ==============================================================================
DHCP_SERVER_IP = '10.0.100.6'
ROTATED_PASSWORD_FILE = "/home/student/lab1/rotated_passwords.csv"
GOLDEN_CONFIG_FOLDER = "/home/student/lab1/pythonscripts/golden_configs/"
# Assuming NMAS is 10.0.100.1 (or whichever IP it uses on the management network)
ZTP_FILE_SERVER_IP = '10.0.100.1' 
# This is the directory Nginx/Apache serves content from
ZTP_FILE_DIR = '/var/www/ztp/configs' 
ZTP_SCRIPT_NAME = 'ztp_bootstrap.py'

def get_dhcp_password():
    """Reads the CSV file and returns the password for the DHCP server (10.0.100.6)."""
    try:
        with open(ROTATED_PASSWORD_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Device'] == DHCP_SERVER_IP:
                    # Assuming the header is 'New_Password'
                    return row['New_Password'] 
        return None
    except FileNotFoundError:
        print(f"Error: Password file not found at {ROTATED_PASSWORD_FILE}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error reading password CSV: {e}", file=sys.stderr)
        return None

def push_dhcp_config(device_mac, device_name, mgmt_ip, dhcp_password, subnet="10.0.100.0/24"):
    """
    Push ZTP DHCP host entry to Arista EOS via NAPALM.
    Replaces Netmiko version.
    """
    try:
        from napalm import get_network_driver

        driver = get_network_driver("eos")
        optional_args = {"transport": "ssh"}

        with driver(
            hostname=DHCP_SERVER_IP,
            username="admin",
            password=dhcp_password,
            optional_args=optional_args
        ) as device:

            # URL for the ZTP bootstrap script
            bootstrap_url = f"http://{ZTP_FILE_SERVER_IP}/configs/{ZTP_SCRIPT_NAME}"

            # Proper EOS DHCP config syntax
            config_lines = [
                f"dhcp server",
                f"   subnet {subnet}",
                f"      reservations",
                f"         mac-address {device_mac}",
                f"           ipv4-address {mgmt_ip}",
                f"         bootfile-name {bootstrap_url}",
                f"         option ipv4 66 server {ZTP_FILE_SERVER_IP}"
            ]

            # Push configuration using merge mode
            device.load_merge_candidate(config="\n".join(config_lines))
            diffs = device.compare_config()
            if diffs:
                device.commit_config()
                print(f"✅ DHCP Config Push Successful for {device_name}:\n{diffs}")
            else:
                print(f"ℹ️ No changes required for {device_name}")
                device.discard_config()

            return True

    except Exception as e:
        print(f"❌ Failed to push DHCP config via NAPALM: {e}", file=sys.stderr)
        return False
# ==============================================================================
# FLASK ROUTES
# ==============================================================================

@app.route('/')
def index():
    return render_template('index.html', templates=templates, devices=devices)

@app.route('/add', methods=['POST'])
def add_device():
    try:
        # Gather form data
        form = request.form.to_dict()
        
        # Collect interfaces dynamically
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

        # --- ASSUMPTION: Get required ZTP parameters from the form ---
        device_mac = form.get('mac_address') # New required field
        mgmt_ip = form.get('management_ip')         # New required field

        # Prepare variables for Jinja2 template
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
            ] if form.get('vlan_id_0') else [],
            # Include ZTP parameters for potential use in the config template
            'management_ip': mgmt_ip
        }
        # --- END ASSUMPTION ---

        # Load the selected template
        template_name = form.get('j2_template')
        template = env.get_template(template_name)

        # Render the configuration
        rendered_config = template.render(template_vars)
        
        # ======================================================================
        # ZTP AUTOMATION START
        # ======================================================================
        device_name = template_vars.get('device_name')
        
        # 1. Validation for ZTP
        if not device_mac or not mgmt_ip or not device_name:
            flash("MAC Address, Management IP, and Device Name are required for ZTP.", "error")
            return redirect(url_for('index'))

        # 2. Save Configuration File on NMAS (HTTP/TFTP Server)
        config_filename = f"{device_name}-startup-config.cfg"
        config_path = os.path.join(ZTP_FILE_DIR, config_filename)
        
        try:
            os.makedirs(ZTP_FILE_DIR, exist_ok=True)
            with open(config_path, 'w') as f:
                f.write(rendered_config)
            flash(f"Configuration saved to {config_path}", "success")
            
            # NOTE: ZTP_SCRIPT_NAME (ztp_bootstrap.py) must be manually placed 
            # in {ZTP_FILE_DIR} and be configured to download this new config file.

        except Exception as e:
            flash(f"Failed to save configuration file to ZTP directory: {e}", "error")
            # Continue to DHCP push, as this is critical

        # 3. Get DHCP Password
        dhcp_password = get_dhcp_password()
        if not dhcp_password:
            flash("Failed to retrieve DHCP server password for ZTP push.", "error")
            return redirect(url_for('index'))

        # 4. Push DHCP Configuration to the Router (10.0.100.6)
        if push_dhcp_config(device_mac, device_name, mgmt_ip, dhcp_password):
            flash(f"ZTP entry successfully configured on DHCP server ({DHCP_SERVER_IP}). New router is ready for ZTP.", "success")
        else:
            flash("Failed to push ZTP configuration to DHCP server. Check NAPALM logs.", "error")

        # ======================================================================
        # ZTP AUTOMATION END
        # ======================================================================

        # Show the rendered config on a new page
        return render_template('rendered_config.html', config=rendered_config)

    except Exception as e:
        flash(f"Error rendering configuration: {e}", "error")
        return redirect(url_for('index'))


# ==============================================================================
# EXISTING CODE BELOW (UNCHANGED)
# ==============================================================================

ROTATED_PASSWORD_FILE = "/home/student/lab1/rotated_passwords.csv"
GOLDEN_CONFIG_FOLDER = "/home/student/lab1/pythonscripts/golden_configs/"

def load_devices_from_csv():
    """Load devices from CSV using column positions (0=IP, 1=Hostname, 2=Username, 3=Password)"""
    devices_list = []
    try:
        with open(ROTATED_PASSWORD_FILE, "r") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
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

GOLDEN_CONFIG_FOLDER = "/home/student/lab1/pythonscripts/netapp/golden_configs"

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
        driver = get_network_driver("eos")  # SSH connection
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

IPAM_CSV = "/home/student/lab1/dynamic_ipam.csv"  # Path to your IPAM CSV

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




if __name__ == '__main__':
    app.run(debug=True)