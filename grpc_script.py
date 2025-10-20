from ncclient import manager
from lxml import etree

devices = [
    {'host': '10.0.100.9', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 'r1'},
    {'host': '10.0.100.6', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 'r2'},
    {'host': '10.0.100.3', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 'r3'},
    {'host': '10.0.100.4', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 'r4'},
    {'host': '10.0.100.8', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 's1'},
    {'host': '10.0.100.7', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 's2'},
    {'host': '10.0.100.2', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 's3'},
    {'host': '10.0.100.5', 'port': 830, 'username': 'admin', 'password': 'pranav', 'name': 's4'},
    
]

# Corrected filters using proper YANG namespaces and syntax
# This filter is for Arista EOS
CPU_FILTER = """
<filter type="subtree">
  <system xmlns="http://openconfig.net/yang/system">
    <cpus>
      <cpu>
        <index>ALL</index>
        <state>
          <total/>
        </state>
      </cpu>
    </cpus>
  </system>
</filter>
"""

# This filter is for Arista EOS
STORAGE_FILTER = """
<filter type="subtree">
  <system xmlns="http://openconfig.net/yang/system">
    <mount-points>
      <mount-point>
        <name/>
        <state>
          <size/>
          <available/>
          <utilized/>
        </state>
      </mount-point>
    </mount-points>
  </system>
</filter>
"""

# This filter is for OpenConfig

INTERFACE_STATUS_FILTER = """
<filter>
  <interfaces xmlns="http://openconfig.net/yang/interfaces">
    <interface>
      <name/>
      <state>
        <oper-status/>
      </state>
    </interface>
  </interfaces>
</filter>
"""

def get_netconf_data(device, filter_xml):
    try:
        with manager.connect(host=device['host'],
                             port=device['port'],
                             username=device['username'],
                             password=device['password'],
                             hostkey_verify=False,
                             device_params={'name': 'default'}) as m:
            response = m.get(filter=filter_xml)
            return etree.tostring(response.data_ele, pretty_print=True).decode()
    except Exception as e:
        return f"[{device['name']}] Error: {e}"

def main():
    for device in devices:
        print(f"\n--- CPU Usage for {device['name']} ---")
        # Assuming Arista EOS namespace for CPU, but this may vary
        print(get_netconf_data(device, CPU_FILTER))
        
        print(f"\n--- Storage Usage for {device['name']} ---")
        # Assuming Arista EOS namespace for storage, but this may vary
        print(get_netconf_data(device, STORAGE_FILTER))
        
        print(f"\n--- Interface Status for {device['name']} ---")
        # Using the OpenConfig namespace for interfaces, as seen in the successful r1 output
        print(get_netconf_data(device, INTERFACE_STATUS_FILTER))

if __name__ == "__main__":
    main()