import csv
import string
import secrets
from netmiko import ConnectHandler

# List of device IPs or hostnames
hosts = [
    "10.0.100.2",
    "10.0.100.3",
    "10.0.100.4",
    "10.0.100.5",
    "10.0.100.6",
    "10.0.100.7",
    "10.0.100.8",
    "10.0.100.9"
]

# Common credentials for all devices (old password)
username = "admin"
old_password = "pranav"
device_type = "arista_eos"

# CSV file to store new passwords
output_file = "rotated_passwords.csv"

# Function to generate a secure random password
def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # ensure at least one lowercase, one uppercase, one digit, one special char
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in string.punctuation for c in password)):
            return password

# Open CSV and write headers
with open(output_file, mode="w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Device", "Username", "New_Password"])

    # Loop through devices
    for host in hosts:
        print(f"Connecting to {host} ...")
        device = {
            "device_type": device_type,
            "host": host,
            "username": username,
            "password": old_password,
        }

        try:
            connection = ConnectHandler(**device)

            # Generate new password
            new_password = generate_password(14)
            print(f"Rotating password for {username}@{host}")

            # Send commands to change password (Arista EOS syntax)
            cmds = [
                "enable",
                "configure terminal",
                f"username {username} secret {new_password}",
                "write memory"
            ]
            for cmd in cmds:
                connection.send_command_timing(cmd)

            connection.disconnect()

            # Write to CSV
            csv_writer.writerow([host, username, new_password])
            print(f"Password rotated for {host}")

        except Exception as e:
            print(f"Failed to rotate password for {host}: {e}")

print(f"\n✅ Password rotation complete. New credentials saved in {output_file}")
