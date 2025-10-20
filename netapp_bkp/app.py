from flask import Flask, render_template, request, redirect, url_for, flash
from jinja2 import Environment, FileSystemLoader
from napalm import get_network_driver
import os
from datetime import datetime

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

# Devices list for Golden Config (use real hostnames/IPs and credentials)
devices = [
    {"device_name": "Router1", "hostname": "10.0.100.9", "username": "admin", "password": "pranav"},
    {"device_name": "Router2", "hostname": "10.0.100.6", "username": "admin", "password": "pranav"},
    {"device_name": "Router3", "hostname": "10.0.100.3", "username": "admin", "password": "pranav"},
    {"device_name": "Router4", "hostname": "10.0.100.4", "username": "admin", "password": "pranav"},
    {"device_name": "Switch1", "hostname": "10.0.100.8", "username": "admin", "password": "pranav"},
    {"device_name": "Switch2", "hostname": "10.0.100.7", "username": "admin", "password": "pranav"},
    {"device_name": "Switch3", "hostname": "10.0.100.2", "username": "admin", "password": "pranav"},
    {"device_name": "Switch4", "hostname": "10.0.100.5", "username": "admin", "password": "pranav"}
]

GOLDEN_CONFIG_FOLDER = "golden_configs"
os.makedirs(GOLDEN_CONFIG_FOLDER, exist_ok=True)

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
            ] if form.get('vlan_id_0') else []
        }

        # Load the selected template
        template_name = form.get('j2_template')
        template = env.get_template(template_name)

        # Render the configuration
        rendered_config = template.render(template_vars)

        # Show the rendered config on a new page
        return render_template('rendered_config.html', config=rendered_config)

    except Exception as e:
        flash(f"Error rendering configuration: {e}", "error")
        return redirect(url_for('index'))

@app.route('/golden_config', methods=['POST'])
def create_golden_config():
    hostname = request.form.get('device_name')
    device = next((d for d in devices if d['hostname'] == hostname), None)
    if not device:
        flash("Device not found!", "error")
        return redirect(url_for('index'))

    try:
        # Select NAPALM driver per device type if needed
        driver = get_network_driver('ios')  # Adjust driver as required per device type
        with driver(hostname=device['hostname'],
                    username=device['username'],
                    password=device['password']) as device_conn:
            running_config = device_conn.get_config()['running']

        # Save to golden_configs folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{device['device_name']}_golden_{timestamp}.cfg"
        filepath = os.path.join(GOLDEN_CONFIG_FOLDER, filename)
        with open(filepath, 'w') as f:
            f.write(running_config)

        flash(f"Golden config saved: {filename}", "success")
    except Exception as e:
        flash(f"Failed to create golden config: {str(e)}", "error")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
