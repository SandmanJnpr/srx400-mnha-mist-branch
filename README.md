# SRX400 MNHA Secure Branch under Juniper Mist

**Eric Sandoval**, Network Security Architect, HPE

An SRX400 MNHA branch design under Juniper Mist, on Junos OS Evolved 25.4X300-D30.3: the paper and the configurations.

| File | What it is |
|---|---|
| [docs/SRX400-MNHA-Secure-Branch-Design.pdf](docs/SRX400-MNHA-Secure-Branch-Design.pdf) | The paper: design, configuration, expected behavior, verification and deployment order. [Open it in the browser](https://sandmanjnpr.github.io/srx400-mnha-mist-branch/docs/SRX400-MNHA-Secure-Branch-Design.pdf) for clickable contents. |
| [mist/srx400-node1.json](mist/srx400-node1.json), [mist/srx400-node2.json](mist/srx400-node2.json) | Mist Hub Profiles for SRX400 node 1 and node 2 (Organization > WAN > Hub Profiles > Import Profile) |
| [mist/vsrx-hub.json](mist/vsrx-hub.json) | Mist Hub Profile for the vSRX hub: the IPsec overlay hub that both SRX400 nodes build their tunnels to |
| [junos/srx400-node1.set](junos/srx400-node1.set), [junos/srx400-node2.set](junos/srx400-node2.set) | Each node's configuration in `display set` form |

Values in angle brackets (`<...>`) are placeholders, and the addresses are examples, node 1's IPv6 /60 included: replace both before use (paper sections 9.1 and 10).

> Reference design by the author, not an official Juniper Networks or HPE position. Verify every line in your own environment before use.
