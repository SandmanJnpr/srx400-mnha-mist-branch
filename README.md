# SRX400 MNHA Secure Branch under Juniper Mist

**Eric Sandoval**, Network Security Architect, HPE

A lab-validated SRX400 MNHA branch design under Juniper Mist: the paper and the configurations.

| File | What it is |
|---|---|
| [docs/SRX400-MNHA-Secure-Branch-Design.pdf](docs/SRX400-MNHA-Secure-Branch-Design.pdf) | The paper: design, configuration, test results and build order |
| [mist/srx400-node1.json](mist/srx400-node1.json), [mist/srx400-node2.json](mist/srx400-node2.json) | Mist Hub Profiles for SRX400 node 1 and node 2 (Organization > WAN > Hub Profiles > Import Profile) |
| [mist/vsrx-hub.json](mist/vsrx-hub.json) | Mist Hub Profile for the vSRX hub |
| [junos/srx400-node1.set](junos/srx400-node1.set), [junos/srx400-node2.set](junos/srx400-node2.set) | Each node's configuration in `display set` form |

Values in angle brackets (`<...>`) are placeholders, and the lab addresses are examples: replace both before use (paper section 10).

> Lab-validated reference by the author, not an official Juniper Networks or HPE position. Verify every line in your own lab before use.
