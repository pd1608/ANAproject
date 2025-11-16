import csv
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Paths
ROTATED_PASSWORDS = "/home/student/lab1/rotated_passwords.csv"
TELEGRAF_CONF = "/etc/telegraf/telegraf.conf"

class TelegrafUpdater(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == ROTATED_PASSWORDS or event.src_path == TELEGRAF_CONF:
            print(f"Detected change in {event.src_path}")
            self.update_telegraf_conf()

    def update_telegraf_conf(self):
        # Read IPs from rotated_passwords.csv
        ips = []
        try:
            with open(ROTATED_PASSWORDS, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ips.append(f'"udp://{row["Device"]}:161"')
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return

        # Read telegraf.conf
        try:
            with open(TELEGRAF_CONF, "r") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading telegraf.conf: {e}")
            return

        # Update agents line
        new_lines = []
        changed = False
        for line in lines:
            if line.strip().startswith("agents = ["):
                new_line = f"agents = [{','.join(ips)}]\n"
                if new_line != line:
                    changed = True
                    print(f"Updating agents line:\n{new_line}")
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        if changed:
            # Write back updated conf
            try:
                with open(TELEGRAF_CONF, "w") as f:
                    f.writelines(new_lines)
                print("telegraf.conf updated successfully!")

                # Restart Telegraf service
                subprocess.run(["sudo", "systemctl", "restart", "telegraf"], check=True)
                print("Telegraf service restarted!")

            except Exception as e:
                print(f"Failed to write conf or restart service: {e}")

if __name__ == "__main__":
    event_handler = TelegrafUpdater()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(ROTATED_PASSWORDS), recursive=False)
    observer.schedule(event_handler, path=os.path.dirname(TELEGRAF_CONF), recursive=False)
    observer.start()
    print("Watching for changes in CSV and telegraf.conf...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
