from scapy.all import *

# Target IP address
target_ip = "8.8.8.8" # Example: Google's DNS server

# Craft the ICMP Echo Request packet
packet = scapy.IP(dst=target_ip)/scapy.ICMP(type="echo-request")

# Send the packet and wait for a single reply
# timeout specifies how long to wait for a reply (in seconds)
# verbose=0 suppresses Scapy's verbose output
print(f"Sending ping to {target_ip}...")
reply = sr1(packet, timeout=1, verbose=0)

# Process the reply
if reply:
    if reply.haslayer(scapy.ICMP) and reply.getlayer(scapy.ICMP).type == 0: # ICMP type 0 is Echo Reply
        print(f"Reply received from {reply.src} (TTL: {reply.ttl})")
    else:
        print(f"Received a reply, but it's not an ICMP Echo Reply from {reply.src}.")
else:
    print("No reply received within the timeout period.")