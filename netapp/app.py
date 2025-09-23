from flask import Flask, render_template, request, redirect, url_for, flash
from napalm import get_network_driver
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecret'

# Example devices list
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
    return render_template('index.html', templates=[
        ('access_router.j2', 'Access Router'),
        ('access_switch.j2', 'Access Switch'),
        ('core_router.j2', 'Core Router'),
        ('core_switch.j2', 'Core Switch')
    ], devices=devices)

@app.route('/add', methods=['POST'])
def add_device():
    # Your existing Add Device logic goes here
    # For simplicity, just redirect back for now
    flash("Device added successfully (simulated)", "success")
    return redirect(url_for('index'))

@app.route('/golden_config', methods=['POST'])
def create_golden_config():
    hostname = request.form.get('device_name')
    device = next((d for d in devices if d['hostname'] == hostname), None)
    if not device:
        flash("Device not found!", "error")
        return redirect(url_for('index'))

    try:
        driver = get_network_driver('ios')  # Adjust driver per device
        with driver(hostname=device['hostname'],
                    username=device['username'],
                    password=device['password']) as device_conn:
            running_config = device_conn.get_config()['running']

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
