#!/usr/bin/env python3
import argparse
import sys
import os
import csv
from jinja2 import Environment, FileSystemLoader
from napalm import get_network_driver

# --- Configuration Paths ---
# NOTE: These paths must be correct relative to where the Jenkins agent executes the script.
TEMPLATE_DIR = '/home/student/lab1/pythonscripts/netapp/templates/' 
ROTATED_PASSWORD_FILE = '/home/student/lab1/rotated_passwords.csv' 

# The load_device_credentials function is omitted/deactivated since credentials are now passed via CLI
# This simplifies the script for the initial ZTP connection.

def deploy_config(device_ip, hostname, template_name, username, password):
    """Renders config and pushes it to the network device."""
    print(f"--- Starting Deployment for {hostname} ({device_ip}) ---")
    
    # --- Step 1: Render Jinja2 Config ---
    try:
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template(template_name)
        
        # Pass necessary variables for template rendering
        template_vars = {'hostname': hostname, 'device_name': hostname} 
        
        rendered_config = template.render(template_vars)
        
        print(f"INFO: Config rendered using {template_name}.")
        
    except Exception as e:
        print(f"FATAL ERROR: Failed to render config from template {template_name}: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Step 2: Push Configuration via NAPALM (Using provided credentials) ---
    try:
        driver = get_network_driver("eos") # Assuming Arista EOS
        
        # Use optional_args to explicitly set transport and enable authentication auto-detection
        optional_args = {
            "transport": "ssh",
            "auth_auto": True 
        }
        
        with driver(
            hostname=device_ip,
            username=username, # Use CLI argument
            password=password, # Use CLI argument
            optional_args=optional_args
        ) as device_conn:
            
            # Load candidate config
            device_conn.load_merge_candidate(config=rendered_config)
            
            # Compare/Confirm
            diff = device_conn.compare_config()
            if not diff:
                print("SUCCESS: No changes detected. Configuration is already up-to-date.")
            else:
                print("INFO: Configuration Diff:")
                print(diff)
                
                # Commit config
                device_conn.commit_config()
                print("SUCCESS: Configuration committed to device.")
                
    except Exception as e:
        # Include specific connection details for troubleshooting
        print(f"FATAL ERROR: Failed to connect or commit config to {device_ip}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # --- Step 0: Parse Command-Line Arguments from Jenkins ---
    parser = argparse.ArgumentParser(description='NAPALM-based network device configuration deployment (ZTP).')
    
    # Existing arguments
    parser.add_argument('--device', required=True, help='Management IP address of the device.')
    parser.add_argument('--hostname', required=True, help='Hostname of the device.')
    parser.add_argument('--template', required=True, help='Jinja2 template file name (e.g., access_router.j2).')
    
    # NEW ARGUMENTS (Required to fix the 'unrecognized arguments' error)
    parser.add_argument('--username', required=True, help='Username for device connection.')
    parser.add_argument('--password', required=True, help='Password for device connection.')
    
    args = parser.parse_args()

    # Execute the deployment logic with all parsed arguments
    deploy_config(args.device, args.hostname, args.template, args.username, args.password)

    # Exit cleanly if successful
    sys.exit(0)