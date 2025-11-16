from napalm import get_network_driver

driver = get_network_driver("eos")

device = driver(
    hostname="10.0.100.6",
    username="admin",
    password="QPqfkleHnpY2QZjz",
    optional_args={"transport": "ssh"},
)

device.open()
print("Connected!")

print(device.get_facts())
device.close()