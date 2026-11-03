# Security zones and the inter-node transit link (zone ICD)

This page answers two questions about the SRX400 MNHA pair in the paper
"SRX400 MNHA Secure Branch Design": how the security zones are mapped on each node, and how the
link between the nodes on `ge-0/0/5` (security zone `ICD`, BGP group `ICD`) is built.

Every configuration line below is quoted from `junos/srx400-node1.set` and
`junos/srx400-node2.set` (the lab's as-built configuration of each node with the generic values
substituted, see the README), or, for `delete` lines, from
`mist/additional-cli/srx400-node1.txt` and `srx400-node2.txt` (a `delete` line never appears in
`display set`). Each quote is split into:

- **Mist native settings** - lines Mist renders from the Hub Profile fields (ports, networks,
  application policies, VPN), and
- **Additional CLI** - lines carried in the profile's Additional CLI
  (`mist/additional-cli/srx400-node1.txt`, `srx400-node2.txt`).

Paper sections are given as (paper 5.4) and so on.

## 1. Naming: ICL, ICD and the transit link

| Item | Port | Node 1 | Node 2 | Zone | Routing instance |
|---|---|---|---|---|---|
| MNHA ICL (session sync, MNHA control) and the MNHA forwarding path | `ge-0/0/4` | 10.255.0.1/30 | 10.255.0.2/30 | `HA` | master (inet.0) |
| MNHA forwarding addresses (`local-forwarding-ip` / `peer-forwarding-ip`) | `lo0.0` | 10.255.1.1/32 | 10.255.1.2/32 | `HA` | master (inet.0) |
| Mist router-id loopback (group `top`), on the same unit | `lo0.0` | 100.100.0.1/32 | 100.100.0.2/32 | `HA` | master (inet.0) |
| Inter-node transit link (eBGP, cross-node traffic) | `ge-0/0/5` | 10.255.2.1/30 | 10.255.2.2/30 | `ICD` | `WAN-VR` |
| WAN (Mist WAN port, DHCP) | `ge-0/0/2` | ISP 1, name `wan` | ISP 2, name `wan2` | `wan` / `wan2` | `WAN-VR` (LAB ONLY) |
| LAN trunk (six tenant units: 0 untagged for MGMT, 20-60 = VLAN id) | `ge-0/0/3` | node address .2 | node address .3 | one zone per tenant | `lan`, and `GUEST-VR` for unit 30 |
| Overlay tunnel and loopback | `st0.0`, `lo0.1` | 100.65.0.2/18, 100.101.0.1 | 100.65.0.3/18, 100.101.0.2 | `vpn_OrgOverlay` | `vpn_OrgOverlay` |
| Out-of-band management | `re0:mgmt-0` | `<NODE1-MGMT-IP>` | `<NODE2-MGMT-IP>` | none | master (inet.0) |

The paper calls `ge-0/0/5` the inter-node transit link. Its security zone and its BGP group are
named `ICD`, and its NAT rule-sets are `ICD_to_wan` / `ICD_to_wan2`. It is not the MNHA ICD: MNHA
does not track it, and the MNHA forwarding path runs on the ICL (`peer-forwarding-ip interface
ge-0/0/4.0`). The "Peer ICD" line in `show chassis high-availability information` is that
forwarding path on the ICL (paper 7). The interface description on `ge-0/0/5` reads
"inter-node transit link to SRX400-2" on node 1 and "inter-node transit link to SRX400-1" on node 2.

`lo0.0` carries both the MNHA forwarding address (Additional CLI) and Mist's router-id loopback
100.100.0.x/32 (Mist native, group `top`). Zone `HA` accepts all host-inbound traffic on
`lo0.0`, so that applies to both addresses.

Node 1 - Mist native settings (rendered by Mist from the Hub Profile):

```
set interfaces ge-0/0/2 unit 0 family inet dhcp vendor-id Juniper
set interfaces lo0 unit 1 family inet address 100.101.0.1/32
set interfaces st0 unit 0 multipoint
set interfaces st0 unit 0 family inet address 100.65.0.2/18
```

Node 1 - Additional CLI:

```
set interfaces ge-0/0/4 description "MNHA ICL to SRX400-2"
set interfaces ge-0/0/4 unit 0 family inet address 10.255.0.1/30
set interfaces ge-0/0/5 description "inter-node transit link to SRX400-2"
set interfaces ge-0/0/5 unit 0 family inet address 10.255.2.1/30
set interfaces lo0 unit 0 family inet address 10.255.1.1/32
```

Node 2 - Mist native settings (rendered by Mist from the Hub Profile):

```
set interfaces ge-0/0/2 unit 0 family inet dhcp vendor-id Juniper
set interfaces lo0 unit 1 family inet address 100.101.0.2/32
set interfaces st0 unit 0 multipoint
set interfaces st0 unit 0 family inet address 100.65.0.3/18
```

Node 2 - Additional CLI:

```
set interfaces ge-0/0/4 description "MNHA ICL to SRX400-1"
set interfaces ge-0/0/4 unit 0 family inet address 10.255.0.2/30
set interfaces ge-0/0/5 description "inter-node transit link to SRX400-1"
set interfaces ge-0/0/5 unit 0 family inet address 10.255.2.2/30
set interfaces lo0 unit 0 family inet address 10.255.1.2/32
```

## 2. Security zones

### Node 1

| Zone | Interfaces | Host-inbound traffic | Other | Purpose |
|---|---|---|---|---|
| `wan` | `ge-0/0/2.0` | zone: system-services dhcp; zone: system-services ike | tcp-rst, screen untrust-screen | ISP 1 WAN (ge-0/0/2, DHCP); the node 1 Mist WAN port named wan |
| `CORP` | `ge-0/0/3.20` | zone: system-services dhcp | tcp-rst | tenant CORP, VLAN 20 |
| `GUEST` | `ge-0/0/3.30` | zone: system-services dhcp | tcp-rst | tenant GUEST, VLAN 30 (routing instance GUEST-VR) |
| `IOT` | `ge-0/0/3.60` | zone: system-services dhcp | tcp-rst | tenant IOT, VLAN 60 (the tenant on the overlay) |
| `MEDIA` | `ge-0/0/3.40` | zone: system-services dhcp | tcp-rst | tenant MEDIA, VLAN 40 |
| `MGMT` | `ge-0/0/3.0` | zone: system-services dhcp | tcp-rst | tenant MGMT, VLAN 10 untagged on the LAN trunk |
| `SECURITY` | `ge-0/0/3.50` | zone: system-services dhcp | tcp-rst | tenant SECURITY, VLAN 50 |
| `vpn_OrgOverlay` | `lo0.1`, `st0.0` | zone: system-services all; zone: protocols all | tcp-rst | IPsec overlay to the hub (st0.0) and the overlay loopback lo0.1 |
| `HA` | `ge-0/0/4.0`, `lo0.0` | ge-0/0/4.0: system-services all; ge-0/0/4.0: protocols all; lo0.0: system-services all; lo0.0: protocols all | - | MNHA ICL (ge-0/0/4) and the MNHA forwarding addresses on lo0.0 |
| `ICD` | `ge-0/0/5.0` | ge-0/0/5.0: system-services all; ge-0/0/5.0: protocols all | - | inter-node transit link ge-0/0/5 (eBGP between the nodes, cross-node traffic) |

### Node 2

| Zone | Interfaces | Host-inbound traffic | Other | Purpose |
|---|---|---|---|---|
| `wan2` | `ge-0/0/2.0` | zone: system-services dhcp; zone: system-services ike | tcp-rst, screen untrust-screen | ISP 2 WAN (ge-0/0/2, DHCP); the node 2 Mist WAN port named wan2 |
| `CORP` | `ge-0/0/3.20` | zone: system-services dhcp | tcp-rst | tenant CORP, VLAN 20 |
| `GUEST` | `ge-0/0/3.30` | zone: system-services dhcp | tcp-rst | tenant GUEST, VLAN 30 (routing instance GUEST-VR) |
| `IOT` | `ge-0/0/3.60` | zone: system-services dhcp | tcp-rst | tenant IOT, VLAN 60 (the tenant on the overlay) |
| `MEDIA` | `ge-0/0/3.40` | zone: system-services dhcp | tcp-rst | tenant MEDIA, VLAN 40 |
| `MGMT` | `ge-0/0/3.0` | zone: system-services dhcp | tcp-rst | tenant MGMT, VLAN 10 untagged on the LAN trunk |
| `SECURITY` | `ge-0/0/3.50` | zone: system-services dhcp | tcp-rst | tenant SECURITY, VLAN 50 |
| `vpn_OrgOverlay` | `lo0.1`, `st0.0` | zone: system-services all; zone: protocols all | tcp-rst | IPsec overlay to the hub (st0.0) and the overlay loopback lo0.1 |
| `HA` | `ge-0/0/4.0`, `lo0.0` | ge-0/0/4.0: system-services all; ge-0/0/4.0: protocols all; lo0.0: system-services all; lo0.0: protocols all | - | MNHA ICL (ge-0/0/4) and the MNHA forwarding addresses on lo0.0 |
| `ICD` | `ge-0/0/5.0` | ge-0/0/5.0: system-services all; ge-0/0/5.0: protocols all | - | inter-node transit link ge-0/0/5 (eBGP between the nodes, cross-node traffic) |

The tenant zones, the WAN zone and `vpn_OrgOverlay` are Mist native: Mist names a tenant zone after
its network, the WAN zone after the WAN port name (`wan` on node 1, `wan2` on node 2), and creates
`vpn_OrgOverlay` for the OrgOverlay VPN. Zones `HA` and `ICD` exist only in the Additional CLI.
Mist also renders the screen `untrust-screen` on the WAN zone and `tcp-rst` on its own zones.

### Tenant, WAN and overlay zones (Mist native)

Node 1 - Mist native settings (rendered by Mist from the Hub Profile):

```
set security zones security-zone wan tcp-rst
set security zones security-zone wan screen untrust-screen
set security zones security-zone wan host-inbound-traffic system-services dhcp
set security zones security-zone wan host-inbound-traffic system-services ike
set security zones security-zone wan interfaces ge-0/0/2.0
set security zones security-zone CORP tcp-rst
set security zones security-zone CORP host-inbound-traffic system-services dhcp
set security zones security-zone CORP interfaces ge-0/0/3.20
set security zones security-zone GUEST tcp-rst
set security zones security-zone GUEST host-inbound-traffic system-services dhcp
set security zones security-zone GUEST interfaces ge-0/0/3.30
set security zones security-zone IOT tcp-rst
set security zones security-zone IOT host-inbound-traffic system-services dhcp
set security zones security-zone IOT interfaces ge-0/0/3.60
set security zones security-zone MEDIA tcp-rst
set security zones security-zone MEDIA host-inbound-traffic system-services dhcp
set security zones security-zone MEDIA interfaces ge-0/0/3.40
set security zones security-zone MGMT tcp-rst
set security zones security-zone MGMT host-inbound-traffic system-services dhcp
set security zones security-zone MGMT interfaces ge-0/0/3.0
set security zones security-zone SECURITY tcp-rst
set security zones security-zone SECURITY host-inbound-traffic system-services dhcp
set security zones security-zone SECURITY interfaces ge-0/0/3.50
set security zones security-zone vpn_OrgOverlay tcp-rst
set security zones security-zone vpn_OrgOverlay host-inbound-traffic system-services all
set security zones security-zone vpn_OrgOverlay host-inbound-traffic protocols all
set security zones security-zone vpn_OrgOverlay interfaces lo0.1
set security zones security-zone vpn_OrgOverlay interfaces st0.0
```

Node 2 - Mist native settings (rendered by Mist from the Hub Profile):

```
set security zones security-zone wan2 tcp-rst
set security zones security-zone wan2 screen untrust-screen
set security zones security-zone wan2 host-inbound-traffic system-services dhcp
set security zones security-zone wan2 host-inbound-traffic system-services ike
set security zones security-zone wan2 interfaces ge-0/0/2.0
set security zones security-zone CORP tcp-rst
set security zones security-zone CORP host-inbound-traffic system-services dhcp
set security zones security-zone CORP interfaces ge-0/0/3.20
set security zones security-zone GUEST tcp-rst
set security zones security-zone GUEST host-inbound-traffic system-services dhcp
set security zones security-zone GUEST interfaces ge-0/0/3.30
set security zones security-zone IOT tcp-rst
set security zones security-zone IOT host-inbound-traffic system-services dhcp
set security zones security-zone IOT interfaces ge-0/0/3.60
set security zones security-zone MEDIA tcp-rst
set security zones security-zone MEDIA host-inbound-traffic system-services dhcp
set security zones security-zone MEDIA interfaces ge-0/0/3.40
set security zones security-zone MGMT tcp-rst
set security zones security-zone MGMT host-inbound-traffic system-services dhcp
set security zones security-zone MGMT interfaces ge-0/0/3.0
set security zones security-zone SECURITY tcp-rst
set security zones security-zone SECURITY host-inbound-traffic system-services dhcp
set security zones security-zone SECURITY interfaces ge-0/0/3.50
set security zones security-zone vpn_OrgOverlay tcp-rst
set security zones security-zone vpn_OrgOverlay host-inbound-traffic system-services all
set security zones security-zone vpn_OrgOverlay host-inbound-traffic protocols all
set security zones security-zone vpn_OrgOverlay interfaces lo0.1
set security zones security-zone vpn_OrgOverlay interfaces st0.0
```

### Zone HA: the ICL and the forwarding addresses (paper 4.4)

Node 1 and node 2 (identical) - Additional CLI:

```
set security zones security-zone HA interfaces ge-0/0/4.0 host-inbound-traffic system-services all
set security zones security-zone HA interfaces ge-0/0/4.0 host-inbound-traffic protocols all
set security zones security-zone HA interfaces lo0.0 host-inbound-traffic system-services all
set security zones security-zone HA interfaces lo0.0 host-inbound-traffic protocols all
```

### Zone ICD: the transit link (paper 5.4)

Node 1 and node 2 (identical) - Additional CLI:

```
set security zones security-zone ICD interfaces ge-0/0/5.0 host-inbound-traffic system-services all
set security zones security-zone ICD interfaces ge-0/0/5.0 host-inbound-traffic protocols all
```

As built, zone `ICD` accepts all host-inbound services and protocols. Restricting it is listed
as not yet tested (paper 9, "Transit link exposure").

## 3. Zone policies

Policy order within a zone pair is the order in the tables. Mist also renders the global policy
`allow_mist` (tenant zones to the Mist cloud, ports 443/2200/2083/6514) and `default-policy
deny-all`; they are not repeated here.

### Node 1

| From zone | To zone | Policy (in order) | Action |
|---|---|---|---|
| `CORP` | `CORP` | `same_zone` | permit |
| `GUEST` | `GUEST` | `same_zone` | permit |
| `IOT` | `IOT` | `same_zone` | permit |
| `MEDIA` | `MEDIA` | `same_zone` | permit |
| `MGMT` | `MGMT` | `same_zone` | permit |
| `SECURITY` | `SECURITY` | `same_zone` | permit |
| `vpn_OrgOverlay` | `vpn_OrgOverlay` | `same_zone` | permit |
| `IOT` | `vpn_OrgOverlay` | `01_allow-to-hub` | permit |
| `MGMT` | `wan` | `01_Internet` | permit |
| `CORP` | `wan` | `01_Internet` | permit |
| `GUEST` | `wan` | `01_Internet` | permit |
| `MEDIA` | `wan` | `01_Internet` | permit |
| `SECURITY` | `wan` | `01_Internet` | permit |
| `IOT` | `wan` | `GEO-BLOCK-DE` | deny |
| `IOT` | `wan` | `01_Internet` | permit |
| `HA` | `HA` | `allow-ha` | permit |
| `MGMT` | `ICD` | `MGMT-xnode` | permit |
| `CORP` | `ICD` | `CORP-xnode` | permit |
| `GUEST` | `ICD` | `GUEST-xnode` | permit |
| `MEDIA` | `ICD` | `MEDIA-xnode` | permit |
| `SECURITY` | `ICD` | `SECURITY-xnode` | permit |
| `IOT` | `ICD` | `GEO-BLOCK-DE` | deny |
| `IOT` | `ICD` | `IOT-xnode` | permit |
| `ICD` | `wan` | `xnode-out` | permit |
| `ICD` | `vpn_OrgOverlay` | `xnode-iot` | permit |

### Node 2

| From zone | To zone | Policy (in order) | Action |
|---|---|---|---|
| `CORP` | `CORP` | `same_zone` | permit |
| `GUEST` | `GUEST` | `same_zone` | permit |
| `IOT` | `IOT` | `same_zone` | permit |
| `MEDIA` | `MEDIA` | `same_zone` | permit |
| `MGMT` | `MGMT` | `same_zone` | permit |
| `SECURITY` | `SECURITY` | `same_zone` | permit |
| `vpn_OrgOverlay` | `vpn_OrgOverlay` | `same_zone` | permit |
| `IOT` | `vpn_OrgOverlay` | `01_allow-to-hub` | permit |
| `MGMT` | `wan2` | `01_Internet` | permit |
| `CORP` | `wan2` | `01_Internet` | permit |
| `GUEST` | `wan2` | `01_Internet` | permit |
| `MEDIA` | `wan2` | `01_Internet` | permit |
| `SECURITY` | `wan2` | `01_Internet` | permit |
| `IOT` | `wan2` | `GEO-BLOCK-DE` | deny |
| `IOT` | `wan2` | `01_Internet` | permit |
| `HA` | `HA` | `allow-ha` | permit |
| `MGMT` | `ICD` | `MGMT-xnode` | permit |
| `CORP` | `ICD` | `CORP-xnode` | permit |
| `GUEST` | `ICD` | `GUEST-xnode` | permit |
| `MEDIA` | `ICD` | `MEDIA-xnode` | permit |
| `SECURITY` | `ICD` | `SECURITY-xnode` | permit |
| `IOT` | `ICD` | `GEO-BLOCK-DE` | deny |
| `IOT` | `ICD` | `IOT-xnode` | permit |
| `ICD` | `wan2` | `xnode-out` | permit |
| `ICD` | `vpn_OrgOverlay` | `xnode-iot` | permit |

### 3.1 HA -> HA (paper 4.4)

Node 1 and node 2 (identical) - Additional CLI:

```
set security policies from-zone HA to-zone HA policy allow-ha match source-address any
set security policies from-zone HA to-zone HA policy allow-ha match destination-address any
set security policies from-zone HA to-zone HA policy allow-ha match application any
set security policies from-zone HA to-zone HA policy allow-ha then permit
```

### 3.2 Tenant -> local WAN and tenant -> overlay (Mist native)

Mist renders one `01_Internet` permit per tenant zone toward the node's own WAN zone (application
policy `Internet`), and `01_allow-to-hub` from IOT to `vpn_OrgOverlay` (application policy
`allow-to-hub`, application `HUB-SITE-NETS` = 10.200.0.0/16). On IOT -> WAN, the Additional
CLI deletes Mist's `01_Internet` and sets it again after `GEO-BLOCK-DE`, so that the deny is
first (paper 5.1); those re-set lines are therefore Additional CLI.

Node 1 - Mist native settings (rendered by Mist from the Hub Profile):

```
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match source-address 10-10-60-0_24
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match destination-address 10-200-0-0_16
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match application any
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match dynamic-application any
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub then permit
set security policies from-zone MGMT to-zone wan policy 01_Internet match source-address 10-10-10-0_24
set security policies from-zone MGMT to-zone wan policy 01_Internet match destination-address any
set security policies from-zone MGMT to-zone wan policy 01_Internet match application any
set security policies from-zone MGMT to-zone wan policy 01_Internet match dynamic-application any
set security policies from-zone MGMT to-zone wan policy 01_Internet then permit
set security policies from-zone CORP to-zone wan policy 01_Internet match source-address 10-10-20-0_24
set security policies from-zone CORP to-zone wan policy 01_Internet match destination-address any
set security policies from-zone CORP to-zone wan policy 01_Internet match application any
set security policies from-zone CORP to-zone wan policy 01_Internet match dynamic-application any
set security policies from-zone CORP to-zone wan policy 01_Internet then permit
set security policies from-zone GUEST to-zone wan policy 01_Internet match source-address 10-10-30-0_24
set security policies from-zone GUEST to-zone wan policy 01_Internet match destination-address any
set security policies from-zone GUEST to-zone wan policy 01_Internet match application any
set security policies from-zone GUEST to-zone wan policy 01_Internet match dynamic-application any
set security policies from-zone GUEST to-zone wan policy 01_Internet then permit
set security policies from-zone MEDIA to-zone wan policy 01_Internet match source-address 10-10-40-0_24
set security policies from-zone MEDIA to-zone wan policy 01_Internet match destination-address any
set security policies from-zone MEDIA to-zone wan policy 01_Internet match application any
set security policies from-zone MEDIA to-zone wan policy 01_Internet match dynamic-application any
set security policies from-zone MEDIA to-zone wan policy 01_Internet then permit
set security policies from-zone SECURITY to-zone wan policy 01_Internet match source-address 10-10-50-0_24
set security policies from-zone SECURITY to-zone wan policy 01_Internet match destination-address any
set security policies from-zone SECURITY to-zone wan policy 01_Internet match application any
set security policies from-zone SECURITY to-zone wan policy 01_Internet match dynamic-application any
set security policies from-zone SECURITY to-zone wan policy 01_Internet then permit
```

Node 1 - Additional CLI:

```
set security policies from-zone IOT to-zone wan policy GEO-BLOCK-DE match source-address any
set security policies from-zone IOT to-zone wan policy GEO-BLOCK-DE match destination-address GEO-DE
set security policies from-zone IOT to-zone wan policy GEO-BLOCK-DE match application any
set security policies from-zone IOT to-zone wan policy GEO-BLOCK-DE then deny
set security policies from-zone IOT to-zone wan policy GEO-BLOCK-DE then count
set security policies from-zone IOT to-zone wan policy 01_Internet match source-address 10-10-60-0_24
set security policies from-zone IOT to-zone wan policy 01_Internet match destination-address any
set security policies from-zone IOT to-zone wan policy 01_Internet match application any
set security policies from-zone IOT to-zone wan policy 01_Internet match dynamic-application any
set security policies from-zone IOT to-zone wan policy 01_Internet then permit
```

Node 2 - Mist native settings (rendered by Mist from the Hub Profile):

```
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match source-address 10-10-60-0_24
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match destination-address 10-200-0-0_16
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match application any
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub match dynamic-application any
set security policies from-zone IOT to-zone vpn_OrgOverlay policy 01_allow-to-hub then permit
set security policies from-zone MGMT to-zone wan2 policy 01_Internet match source-address 10-10-10-0_24
set security policies from-zone MGMT to-zone wan2 policy 01_Internet match destination-address any
set security policies from-zone MGMT to-zone wan2 policy 01_Internet match application any
set security policies from-zone MGMT to-zone wan2 policy 01_Internet match dynamic-application any
set security policies from-zone MGMT to-zone wan2 policy 01_Internet then permit
set security policies from-zone CORP to-zone wan2 policy 01_Internet match source-address 10-10-20-0_24
set security policies from-zone CORP to-zone wan2 policy 01_Internet match destination-address any
set security policies from-zone CORP to-zone wan2 policy 01_Internet match application any
set security policies from-zone CORP to-zone wan2 policy 01_Internet match dynamic-application any
set security policies from-zone CORP to-zone wan2 policy 01_Internet then permit
set security policies from-zone GUEST to-zone wan2 policy 01_Internet match source-address 10-10-30-0_24
set security policies from-zone GUEST to-zone wan2 policy 01_Internet match destination-address any
set security policies from-zone GUEST to-zone wan2 policy 01_Internet match application any
set security policies from-zone GUEST to-zone wan2 policy 01_Internet match dynamic-application any
set security policies from-zone GUEST to-zone wan2 policy 01_Internet then permit
set security policies from-zone MEDIA to-zone wan2 policy 01_Internet match source-address 10-10-40-0_24
set security policies from-zone MEDIA to-zone wan2 policy 01_Internet match destination-address any
set security policies from-zone MEDIA to-zone wan2 policy 01_Internet match application any
set security policies from-zone MEDIA to-zone wan2 policy 01_Internet match dynamic-application any
set security policies from-zone MEDIA to-zone wan2 policy 01_Internet then permit
set security policies from-zone SECURITY to-zone wan2 policy 01_Internet match source-address 10-10-50-0_24
set security policies from-zone SECURITY to-zone wan2 policy 01_Internet match destination-address any
set security policies from-zone SECURITY to-zone wan2 policy 01_Internet match application any
set security policies from-zone SECURITY to-zone wan2 policy 01_Internet match dynamic-application any
set security policies from-zone SECURITY to-zone wan2 policy 01_Internet then permit
```

Node 2 - Additional CLI:

```
set security policies from-zone IOT to-zone wan2 policy GEO-BLOCK-DE match source-address any
set security policies from-zone IOT to-zone wan2 policy GEO-BLOCK-DE match destination-address GEO-DE
set security policies from-zone IOT to-zone wan2 policy GEO-BLOCK-DE match application any
set security policies from-zone IOT to-zone wan2 policy GEO-BLOCK-DE then deny
set security policies from-zone IOT to-zone wan2 policy GEO-BLOCK-DE then count
set security policies from-zone IOT to-zone wan2 policy 01_Internet match source-address 10-10-60-0_24
set security policies from-zone IOT to-zone wan2 policy 01_Internet match destination-address any
set security policies from-zone IOT to-zone wan2 policy 01_Internet match application any
set security policies from-zone IOT to-zone wan2 policy 01_Internet match dynamic-application any
set security policies from-zone IOT to-zone wan2 policy 01_Internet then permit
```

The address name `10-200-0-0_16` in `01_allow-to-hub` (and its address-book entry) is a derived
line: it follows Mist's naming for the generic 10.200.0.0/16 application and was not captured from
a render of that generic object (README, "Notes on the configurations").

### 3.3 Tenant -> ICD: the ingress node sends traffic to the peer (paper 5.4)

One permit per tenant zone, on both nodes. On IOT -> ICD, `GEO-BLOCK-DE` is listed first
(paper 5.1). No source NAT is applied on this hop; the egress node translates (section 4.9).

Node 1 and node 2 (identical) - Additional CLI:

```
set security policies from-zone MGMT to-zone ICD policy MGMT-xnode match source-address any
set security policies from-zone MGMT to-zone ICD policy MGMT-xnode match destination-address any
set security policies from-zone MGMT to-zone ICD policy MGMT-xnode match application any
set security policies from-zone MGMT to-zone ICD policy MGMT-xnode then permit
set security policies from-zone CORP to-zone ICD policy CORP-xnode match source-address any
set security policies from-zone CORP to-zone ICD policy CORP-xnode match destination-address any
set security policies from-zone CORP to-zone ICD policy CORP-xnode match application any
set security policies from-zone CORP to-zone ICD policy CORP-xnode then permit
set security policies from-zone GUEST to-zone ICD policy GUEST-xnode match source-address any
set security policies from-zone GUEST to-zone ICD policy GUEST-xnode match destination-address any
set security policies from-zone GUEST to-zone ICD policy GUEST-xnode match application any
set security policies from-zone GUEST to-zone ICD policy GUEST-xnode then permit
set security policies from-zone MEDIA to-zone ICD policy MEDIA-xnode match source-address any
set security policies from-zone MEDIA to-zone ICD policy MEDIA-xnode match destination-address any
set security policies from-zone MEDIA to-zone ICD policy MEDIA-xnode match application any
set security policies from-zone MEDIA to-zone ICD policy MEDIA-xnode then permit
set security policies from-zone SECURITY to-zone ICD policy SECURITY-xnode match source-address any
set security policies from-zone SECURITY to-zone ICD policy SECURITY-xnode match destination-address any
set security policies from-zone SECURITY to-zone ICD policy SECURITY-xnode match application any
set security policies from-zone SECURITY to-zone ICD policy SECURITY-xnode then permit
set security policies from-zone IOT to-zone ICD policy GEO-BLOCK-DE match source-address any
set security policies from-zone IOT to-zone ICD policy GEO-BLOCK-DE match destination-address GEO-DE
set security policies from-zone IOT to-zone ICD policy GEO-BLOCK-DE match application any
set security policies from-zone IOT to-zone ICD policy GEO-BLOCK-DE then deny
set security policies from-zone IOT to-zone ICD policy GEO-BLOCK-DE then count
set security policies from-zone IOT to-zone ICD policy IOT-xnode match source-address any
set security policies from-zone IOT to-zone ICD policy IOT-xnode match destination-address any
set security policies from-zone IOT to-zone ICD policy IOT-xnode match application any
set security policies from-zone IOT to-zone ICD policy IOT-xnode then permit
```

### 3.4 ICD -> local WAN: the egress node takes the peer's traffic to its own ISP (paper 5.4)

Node 1 - Additional CLI:

```
set security policies from-zone ICD to-zone wan policy xnode-out match source-address any
set security policies from-zone ICD to-zone wan policy xnode-out match destination-address any
set security policies from-zone ICD to-zone wan policy xnode-out match application any
set security policies from-zone ICD to-zone wan policy xnode-out then permit
```

Node 2 - Additional CLI:

```
set security policies from-zone ICD to-zone wan2 policy xnode-out match source-address any
set security policies from-zone ICD to-zone wan2 policy xnode-out match destination-address any
set security policies from-zone ICD to-zone wan2 policy xnode-out match application any
set security policies from-zone ICD to-zone wan2 policy xnode-out then permit
```

### 3.5 ICD -> vpn_OrgOverlay: the peer's traffic into this node's tunnel to the hub (paper 5.4)

Node 1 and node 2 (identical) - Additional CLI:

```
set security policies from-zone ICD to-zone vpn_OrgOverlay policy xnode-iot match source-address any
set security policies from-zone ICD to-zone vpn_OrgOverlay policy xnode-iot match destination-address any
set security policies from-zone ICD to-zone vpn_OrgOverlay policy xnode-iot match application any
set security policies from-zone ICD to-zone vpn_OrgOverlay policy xnode-iot then permit
```

### 3.6 Directions with no policy

There is no policy from `ICD` to a tenant zone, from a WAN zone to `ICD`, from `vpn_OrgOverlay`
to a tenant zone (traffic that the hub site starts toward a tenant is denied by
`default-policy deny-all`; only IOT -> `vpn_OrgOverlay` and its replies are permitted), or
between `HA` and any other zone. Replies travel on the session that the first packet created: on the ingress node the
tenant -> `ICD` session, on the egress node the `ICD` -> WAN (or `ICD` -> `vpn_OrgOverlay`)
session. As built, the cross-node policies match any source, destination and application;
scoping them is not yet tested (paper 5.4, 9).

## 4. The transit link design

### 4.1 Interface and routing instance WAN-VR (paper 5.4)

`ge-0/0/5` and the WAN port `ge-0/0/2` sit in the virtual router `WAN-VR`. Placing the WAN in
`WAN-VR` is LAB ONLY: it keeps the WAN out of inet.0, which holds the out-of-band management
default in the lab. A build with the WAN in inet.0 is not tested (paper 5.4, 9).

Node 1 - Additional CLI:

```
set routing-instances WAN-VR instance-type virtual-router
set routing-instances WAN-VR routing-options router-id 10.255.2.1
set routing-instances WAN-VR routing-options autonomous-system 65001
set routing-instances WAN-VR routing-options static route 10.10.10.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.10.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.20.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.20.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.30.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.30.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.40.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.40.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.50.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.50.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.60.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.60.0/24 preference 250
set routing-instances WAN-VR routing-options instance-import HUB-FROM-OVERLAY
set routing-instances WAN-VR interface ge-0/0/2.0
set routing-instances WAN-VR interface ge-0/0/5.0
```

Node 2 - Additional CLI:

```
set routing-instances WAN-VR instance-type virtual-router
set routing-instances WAN-VR routing-options router-id 10.255.2.2
set routing-instances WAN-VR routing-options autonomous-system 65002
set routing-instances WAN-VR routing-options static route 10.10.10.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.10.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.20.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.20.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.30.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.30.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.40.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.40.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.50.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.50.0/24 preference 250
set routing-instances WAN-VR routing-options static route 10.10.60.0/24 discard
set routing-instances WAN-VR routing-options static route 10.10.60.0/24 preference 250
set routing-instances WAN-VR routing-options instance-import HUB-FROM-OVERLAY
set routing-instances WAN-VR interface ge-0/0/2.0
set routing-instances WAN-VR interface ge-0/0/5.0
```

The tenant /24 discard routes (preference 250) exist only to be exported to the peer, and only
while the node is SRG1-active (term `lan` of `WAN-EXPORT`, section 4.4). `instance-import
HUB-FROM-OVERLAY` copies the hub-site routes from this node's own tunnel into `WAN-VR`
(section 4.7).

### 4.2 eBGP group ICD (paper 5.4)

| Value | Node 1 | Node 2 |
|---|---|---|
| Routing instance | `WAN-VR` | `WAN-VR` |
| Local AS (`WAN-VR` autonomous-system) | 65001 | 65002 |
| Peer AS / neighbor | 65002 / 10.255.2.2 | 65001 / 10.255.2.1 |
| Router ID | 10.255.2.1 | 10.255.2.2 |
| BFD | 300 ms x 3 | 300 ms x 3 |
| Import / export | `ICD-IMPORT` / `WAN-EXPORT` | `ICD-IMPORT` / `WAN-EXPORT` |
| Received routes go to | rib-group `WAN-LEAK` | rib-group `WAN-LEAK` |

Node 1 - Additional CLI:

```
set routing-instances WAN-VR protocols bgp group ICD type external
set routing-instances WAN-VR protocols bgp group ICD import ICD-IMPORT
set routing-instances WAN-VR protocols bgp group ICD family inet unicast rib-group WAN-LEAK
set routing-instances WAN-VR protocols bgp group ICD export WAN-EXPORT
set routing-instances WAN-VR protocols bgp group ICD peer-as 65002
set routing-instances WAN-VR protocols bgp group ICD bfd-liveness-detection minimum-interval 300
set routing-instances WAN-VR protocols bgp group ICD bfd-liveness-detection multiplier 3
set routing-instances WAN-VR protocols bgp group ICD neighbor 10.255.2.2
```

Node 2 - Additional CLI:

```
set routing-instances WAN-VR protocols bgp group ICD type external
set routing-instances WAN-VR protocols bgp group ICD import ICD-IMPORT
set routing-instances WAN-VR protocols bgp group ICD family inet unicast rib-group WAN-LEAK
set routing-instances WAN-VR protocols bgp group ICD export WAN-EXPORT
set routing-instances WAN-VR protocols bgp group ICD peer-as 65001
set routing-instances WAN-VR protocols bgp group ICD bfd-liveness-detection minimum-interval 300
set routing-instances WAN-VR protocols bgp group ICD bfd-liveness-detection multiplier 3
set routing-instances WAN-VR protocols bgp group ICD neighbor 10.255.2.1
```

As built, each profile also sets the master-instance AS to the node's `WAN-VR` AS, which replaces
the AS 65000 that Mist renders in the master instance; the overlay instance then sets AS 65000
itself (paper 5.6). No BGP runs in the master instance.

Node 1 - Mist native settings (rendered by Mist from the Hub Profile):

```
set groups top routing-options autonomous-system 65000
```

Node 1 - Additional CLI:

```
set routing-instances vpn_OrgOverlay routing-options autonomous-system 65000
set routing-options autonomous-system 65001
```

Node 2 - Mist native settings (rendered by Mist from the Hub Profile):

```
set groups top routing-options autonomous-system 65000
```

Node 2 - Additional CLI:

```
set routing-instances vpn_OrgOverlay routing-options autonomous-system 65000
set routing-options autonomous-system 65002
```

### 4.3 Rib-group WAN-LEAK: what the peer's routes reach (paper 5.4)

Every route received from the peer goes into `WAN-VR.inet.0`. Only the peer's 0/0 also goes into
`lan.inet.0` and `GUEST-VR.inet.0`, where it becomes the backup default of the tenants.

Node 1 and node 2 (identical) - Additional CLI:

```
set policy-options policy-statement WAN-LEAK-POL term wan to rib WAN-VR.inet.0
set policy-options policy-statement WAN-LEAK-POL term wan then accept
set policy-options policy-statement WAN-LEAK-POL term default from route-filter 0.0.0.0/0 exact
set policy-options policy-statement WAN-LEAK-POL term default then accept
set policy-options policy-statement WAN-LEAK-POL term end then reject
set routing-options rib-groups WAN-LEAK import-rib WAN-VR.inet.0
set routing-options rib-groups WAN-LEAK import-rib lan.inet.0
set routing-options rib-groups WAN-LEAK import-rib GUEST-VR.inet.0
set routing-options rib-groups WAN-LEAK import-policy WAN-LEAK-POL
```

### 4.4 Export and import policies (identical on both nodes; paper 5.4)

- `WAN-EXPORT` term `default`: the node's own 0/0 in `WAN-VR` (the DHCP default from its ISP).
  Nothing in the configuration tracks the upstream path beyond the DHCP default (paper 9).
- Term `lan`: the six tenant /24 discard routes, only while condition `MNHA-ACTIVE` is true
  (the SRG1 active signal route 10.255.3.1/32 is in inet.0). The peer's `WAN-VR` therefore sends
  cross-node return traffic back to the SRG1-active node.
- Term `hub`: the routes with community `HUB-LOCAL`, which `HUB-FROM-OVERLAY` adds to the
  hub-site routes from this node's own tunnel. `ICD-IMPORT` does not remove the community, so the
  peer's copies carry it too; they are not sent back to the peer because Junos does not advertise
  a route to the eBGP peer it was learned from (no `advertise-peer-as`). Removing `HUB-LOCAL` on
  import is not tested.
- `ICD-IMPORT` sets preference 175 on the peer's hub-site routes, so the node's own copy (BGP 170)
  wins while its own tunnel is up, and accepts everything else unchanged.

Node 1 and node 2 (identical) - Additional CLI:

```
set policy-options policy-statement ICD-IMPORT term hub from route-filter 10.200.0.0/16 orlonger
set policy-options policy-statement ICD-IMPORT term hub then preference 175
set policy-options policy-statement ICD-IMPORT term hub then accept
set policy-options policy-statement ICD-IMPORT term rest then accept
set policy-options policy-statement HUB-FROM-OVERLAY term hub from instance vpn_OrgOverlay
set policy-options policy-statement HUB-FROM-OVERLAY term hub from protocol bgp
set policy-options policy-statement HUB-FROM-OVERLAY term hub from route-filter 10.200.0.0/16 orlonger
set policy-options policy-statement HUB-FROM-OVERLAY term hub then community add HUB-LOCAL
set policy-options policy-statement HUB-FROM-OVERLAY term hub then accept
set policy-options policy-statement HUB-FROM-OVERLAY term end then reject
set policy-options policy-statement WAN-EXPORT term default from route-filter 0.0.0.0/0 exact
set policy-options policy-statement WAN-EXPORT term default then accept
set policy-options policy-statement WAN-EXPORT term lan from protocol static
set policy-options policy-statement WAN-EXPORT term lan from route-filter 10.10.10.0/24 exact
set policy-options policy-statement WAN-EXPORT term lan from route-filter 10.10.20.0/24 exact
set policy-options policy-statement WAN-EXPORT term lan from route-filter 10.10.30.0/24 exact
set policy-options policy-statement WAN-EXPORT term lan from route-filter 10.10.40.0/24 exact
set policy-options policy-statement WAN-EXPORT term lan from route-filter 10.10.50.0/24 exact
set policy-options policy-statement WAN-EXPORT term lan from route-filter 10.10.60.0/24 exact
set policy-options policy-statement WAN-EXPORT term lan from condition MNHA-ACTIVE
set policy-options policy-statement WAN-EXPORT term lan then accept
set policy-options policy-statement WAN-EXPORT term hub from community HUB-LOCAL
set policy-options policy-statement WAN-EXPORT term hub then accept
set policy-options policy-statement WAN-EXPORT term end then reject
set policy-options community HUB-LOCAL members 65000:1000
```

### 4.5 Route preferences

| Route | Table | Preference | Origin |
|---|---|---|---|
| 0/0 next-table `WAN-VR.inet.0` | `lan` on node 1, `GUEST-VR` on node 2 | 5 (static default) | Additional CLI |
| 0/0 next-table `WAN-VR.inet.0` | `lan` on node 2, `GUEST-VR` on node 1 | 200 | Additional CLI |
| 0/0 from the peer over `ge-0/0/5` | `WAN-VR`, `lan`, `GUEST-VR` | 170 (BGP) | rib-group `WAN-LEAK` |
| 0/0 from the node's own ISP | `WAN-VR` | DHCP default | Mist WAN port (DHCP) |
| Tenant /24 discard | `WAN-VR` | 250 | Additional CLI |
| Tenant /24 from the SRG1-active peer | `WAN-VR` | 170 (BGP) | `WAN-EXPORT` term `lan` on the peer |
| Hub site 10.200.0.0/16 from the own tunnel | `vpn_OrgOverlay`, copied to `lan` and `WAN-VR` | 170 (BGP) | Mist overlay; `vpn_OrgOverlay_bgp`, `HUB-FROM-OVERLAY` |
| Hub site from the peer over `ge-0/0/5` | `WAN-VR` | 175 | `ICD-IMPORT` |

### 4.6 How each tenant gets its backup default over the transit link (paper 4.3, 5.4)

| Routing instance (tenants) | Node 1 | Node 2 |
|---|---|---|
| `lan` (MGMT, CORP, MEDIA, SECURITY, IOT) - ISP 1 side | Static 0/0 next-table `WAN-VR`, default preference: exits ISP 1 locally | Static 0/0 next-table `WAN-VR`, preference 200: node 1's BGP 0/0 (170) is preferred, so these tenants exit ISP 1 through node 1 |
| `GUEST-VR` (GUEST) - ISP 2 side | Static 0/0 next-table `WAN-VR`, preference 200: node 2's BGP 0/0 (170) is preferred, so GUEST exits ISP 2 through node 2 | Static 0/0 next-table `WAN-VR`, default preference: exits ISP 2 locally |

When the peer's 0/0 is withdrawn, the local static default (preference 200) takes over and the
tenant leaves by the node's own ISP. Internet traffic on that fallback is not yet tested
(paper 4.3, 9).

Node 1 - Additional CLI:

```
set routing-instances GUEST-VR routing-options static route 0.0.0.0/0 next-table WAN-VR.inet.0
set routing-instances GUEST-VR routing-options static route 0.0.0.0/0 preference 200
set routing-instances lan routing-options static route 0.0.0.0/0 next-table WAN-VR.inet.0
set routing-instances lan routing-options instance-import vpn_OrgOverlay_bgp
```

Node 2 - Additional CLI:

```
set routing-instances GUEST-VR routing-options static route 0.0.0.0/0 next-table WAN-VR.inet.0
set routing-instances lan routing-options static route 0.0.0.0/0 next-table WAN-VR.inet.0
set routing-instances lan routing-options static route 0.0.0.0/0 preference 200
set routing-instances lan routing-options instance-import vpn_OrgOverlay_bgp
```

Every `delete` line in the Additional CLI (node 1 shown) removes part of Mist's render: the
GUEST unit (`ge-0/0/3.30`), its DHCP group and its pool leave Mist's `lan` (they are set again in
`GUEST-VR`); `lan` no longer imports Mist's inet.0 default (`wan_default`); the APBR group is not
applied, so VR routing alone decides the exit; Mist's `dead-peer-detection optimized` is replaced
by `always-send`; and Mist's IOT `01_Internet` is removed so that it can be set again below
`GEO-BLOCK-DE`.

```
delete groups top routing-instances lan interface ge-0/0/3.30
delete groups top routing-instances lan system services dhcp-local-server group GUEST
delete groups top routing-instances lan access address-assignment pool GUEST
delete apply-groups apbr
delete groups top routing-instances lan routing-options instance-import wan_default
delete security ike gateway wan_to_<hub-MAC>_wan dead-peer-detection optimized
delete security policies from-zone IOT to-zone wan policy 01_Internet
```

Node 2 has the same lines, with `wan2_to_<hub-MAC>_wan` in the DPD line and zone `wan2` in the
`01_Internet` line.

### 4.7 Hub-site prefixes (paper 5.4, 5.6)

- The hub advertises 10.200.0.0/16 over the overlay iBGP (`vpn_OrgOverlay`, AS 65000).
- VR `lan` takes the hub-site routes from `vpn_OrgOverlay` through Mist's
  `instance-import vpn_OrgOverlay_bgp`, so each node uses its own tunnel first.
- `HUB-FROM-OVERLAY` copies the same routes into `WAN-VR` with community `HUB-LOCAL`;
  `WAN-EXPORT` term `hub` sends them to the peer; the peer installs them at preference 175.
- When a node's own tunnel is down, VR `lan` has no hub-site route and uses its default. That
  default leads into `WAN-VR`, which still holds the peer's copy (175), so the traffic crosses
  `ge-0/0/5` and the peer forwards it into its own tunnel (policy `ICD` -> `vpn_OrgOverlay`,
  `xnode-iot`). Tested with node 1 active (paper 6.4).
- On the hub, `OVERLAY-IN` rejects 10.255.0.0/16 from the spokes, so the MNHA control and
  transit-link addresses never enter the overlay (paper 4.5).

Node 1 and node 2 (identical) - Mist native settings (rendered by Mist from the Hub Profile):

```
set groups top policy-options policy-statement vpn_OrgOverlay_bgp term 01_bgp from instance vpn_OrgOverlay
set groups top policy-options policy-statement vpn_OrgOverlay_bgp term 01_bgp from protocol bgp
set groups top policy-options policy-statement vpn_OrgOverlay_bgp term 01_bgp then accept
set groups top policy-options policy-statement vpn_OrgOverlay_bgp term 02_not_bgp from instance vpn_OrgOverlay
set groups top policy-options policy-statement vpn_OrgOverlay_bgp term 02_not_bgp then reject
set groups top routing-instances lan routing-options instance-import vpn_OrgOverlay_bgp
set groups top routing-instances vpn_OrgOverlay routing-options instance-import lan_direct
set groups top routing-instances vpn_OrgOverlay routing-options instance-import master_direct
```

Node 1 and node 2 (identical) - Additional CLI:

```
set routing-instances WAN-VR routing-options instance-import HUB-FROM-OVERLAY
set routing-instances lan routing-options instance-import vpn_OrgOverlay_bgp
```

### 4.8 SRG1 signal routes (paper 4.4, 5.6)

SRG1 installs 10.255.3.1/32 in inet.0 on the active node and 10.255.3.2/32 on the backup node.
Condition `MNHA-ACTIVE` tests for 10.255.3.1/32. It is used twice: term `lan` of `WAN-EXPORT`
(only the active node exports the tenant /24s over `ge-0/0/5`) and `IOT-LP` (only the active node
sets local-preference 200 on its IOT route toward the hub, so the hub's return route follows the
active node). The signal routes themselves are not exported anywhere.

Node 1 and node 2 (identical) - Mist native settings (rendered by Mist from the Hub Profile):

```
set groups top routing-instances vpn_OrgOverlay protocols bgp group OrgOverlay_overlay export OrgOverlay_advertise
```

Node 1 and node 2 (identical) - Additional CLI:

```
set chassis high-availability services-redundancy-group 1 active-signal-route 10.255.3.1
set chassis high-availability services-redundancy-group 1 backup-signal-route 10.255.3.2
set policy-options policy-statement IOT-LP term active from condition MNHA-ACTIVE
set policy-options policy-statement IOT-LP term active then local-preference 200
set policy-options condition MNHA-ACTIVE if-route-exists address-family inet 10.255.3.1/32
set policy-options condition MNHA-ACTIVE if-route-exists address-family inet table inet.0
set routing-instances vpn_OrgOverlay protocols bgp group OrgOverlay_overlay export IOT-LP
set routing-instances vpn_OrgOverlay protocols bgp group OrgOverlay_overlay export OrgOverlay_advertise
```

### 4.9 Source NAT tied to the transit link (paper 5.3)

Traffic that crosses `ge-0/0/5` keeps its tenant source address and is translated on the egress
node, by that node's interface address on its own ISP: rule-set `ICD_to_wan` (zone `ICD` -> `wan`)
on node 1, `ICD_to_wan2` (zone `ICD` -> `wan2`) on node 2. Local tenant traffic uses Mist's
per-tenant rule-sets `<tenant>_to_wan` (node 1) and `<tenant>_to_wan2` (node 2). There is no NAT
toward `ICD` or toward `vpn_OrgOverlay`. A NAT pool is not part of this build; per-node pool NAT
is not yet tested (paper 5.3, 9).

Node 1 - Additional CLI:

```
set security nat source rule-set ICD_to_wan from zone ICD
set security nat source rule-set ICD_to_wan to zone wan
set security nat source rule-set ICD_to_wan rule xnode match source-address 0.0.0.0/0
set security nat source rule-set ICD_to_wan rule xnode then source-nat interface
```

Node 2 - Additional CLI:

```
set security nat source rule-set ICD_to_wan2 from zone ICD
set security nat source rule-set ICD_to_wan2 to zone wan2
set security nat source rule-set ICD_to_wan2 rule xnode match source-address 0.0.0.0/0
set security nat source rule-set ICD_to_wan2 rule xnode then source-nat interface
```

The Mist rule-sets for local traffic (one per tenant zone, plus `host_to_wan[2]` for traffic from
the node itself):

Node 1 - Mist native settings (rendered by Mist from the Hub Profile):

```
set security nat source rule-set host_to_wan from zone junos-host
set security nat source rule-set host_to_wan to zone wan
set security nat source rule-set host_to_wan rule host_to_wan match source-address 0.0.0.0/0
set security nat source rule-set host_to_wan rule host_to_wan then source-nat interface
set security nat source rule-set CORP_to_wan from zone CORP
set security nat source rule-set CORP_to_wan to zone wan
set security nat source rule-set CORP_to_wan rule CORP_to_wan match source-address 0.0.0.0/0
set security nat source rule-set CORP_to_wan rule CORP_to_wan then source-nat interface
set security nat source rule-set GUEST_to_wan from zone GUEST
set security nat source rule-set GUEST_to_wan to zone wan
set security nat source rule-set GUEST_to_wan rule GUEST_to_wan match source-address 0.0.0.0/0
set security nat source rule-set GUEST_to_wan rule GUEST_to_wan then source-nat interface
set security nat source rule-set IOT_to_wan from zone IOT
set security nat source rule-set IOT_to_wan to zone wan
set security nat source rule-set IOT_to_wan rule IOT_to_wan match source-address 0.0.0.0/0
set security nat source rule-set IOT_to_wan rule IOT_to_wan then source-nat interface
set security nat source rule-set MEDIA_to_wan from zone MEDIA
set security nat source rule-set MEDIA_to_wan to zone wan
set security nat source rule-set MEDIA_to_wan rule MEDIA_to_wan match source-address 0.0.0.0/0
set security nat source rule-set MEDIA_to_wan rule MEDIA_to_wan then source-nat interface
set security nat source rule-set MGMT_to_wan from zone MGMT
set security nat source rule-set MGMT_to_wan to zone wan
set security nat source rule-set MGMT_to_wan rule MGMT_to_wan match source-address 0.0.0.0/0
set security nat source rule-set MGMT_to_wan rule MGMT_to_wan then source-nat interface
set security nat source rule-set SECURITY_to_wan from zone SECURITY
set security nat source rule-set SECURITY_to_wan to zone wan
set security nat source rule-set SECURITY_to_wan rule SECURITY_to_wan match source-address 0.0.0.0/0
set security nat source rule-set SECURITY_to_wan rule SECURITY_to_wan then source-nat interface
```

Node 2 - Mist native settings (rendered by Mist from the Hub Profile):

```
set security nat source rule-set host_to_wan2 from zone junos-host
set security nat source rule-set host_to_wan2 to zone wan2
set security nat source rule-set host_to_wan2 rule host_to_wan2 match source-address 0.0.0.0/0
set security nat source rule-set host_to_wan2 rule host_to_wan2 then source-nat interface
set security nat source rule-set CORP_to_wan2 from zone CORP
set security nat source rule-set CORP_to_wan2 to zone wan2
set security nat source rule-set CORP_to_wan2 rule CORP_to_wan2 match source-address 0.0.0.0/0
set security nat source rule-set CORP_to_wan2 rule CORP_to_wan2 then source-nat interface
set security nat source rule-set GUEST_to_wan2 from zone GUEST
set security nat source rule-set GUEST_to_wan2 to zone wan2
set security nat source rule-set GUEST_to_wan2 rule GUEST_to_wan2 match source-address 0.0.0.0/0
set security nat source rule-set GUEST_to_wan2 rule GUEST_to_wan2 then source-nat interface
set security nat source rule-set IOT_to_wan2 from zone IOT
set security nat source rule-set IOT_to_wan2 to zone wan2
set security nat source rule-set IOT_to_wan2 rule IOT_to_wan2 match source-address 0.0.0.0/0
set security nat source rule-set IOT_to_wan2 rule IOT_to_wan2 then source-nat interface
set security nat source rule-set MEDIA_to_wan2 from zone MEDIA
set security nat source rule-set MEDIA_to_wan2 to zone wan2
set security nat source rule-set MEDIA_to_wan2 rule MEDIA_to_wan2 match source-address 0.0.0.0/0
set security nat source rule-set MEDIA_to_wan2 rule MEDIA_to_wan2 then source-nat interface
set security nat source rule-set MGMT_to_wan2 from zone MGMT
set security nat source rule-set MGMT_to_wan2 to zone wan2
set security nat source rule-set MGMT_to_wan2 rule MGMT_to_wan2 match source-address 0.0.0.0/0
set security nat source rule-set MGMT_to_wan2 rule MGMT_to_wan2 then source-nat interface
set security nat source rule-set SECURITY_to_wan2 from zone SECURITY
set security nat source rule-set SECURITY_to_wan2 to zone wan2
set security nat source rule-set SECURITY_to_wan2 rule SECURITY_to_wan2 match source-address 0.0.0.0/0
set security nat source rule-set SECURITY_to_wan2 rule SECURITY_to_wan2 then source-nat interface
```

### 4.10 Policy limits (paper 9, "Export and import policy hardening")

As built, these routing policies end open. Filtered versions are not tested.

- The spokes have no import policy on the overlay iBGP. VR `lan` imports every BGP route of
  `vpn_OrgOverlay` through Mist's `vpn_OrgOverlay_bgp` (term `01_bgp`: from instance
  `vpn_OrgOverlay`, protocol bgp, accept). A default route advertised by the hub, for example,
  would therefore be imported into `lan` on both nodes.
- `ICD-IMPORT` ends with term `rest` accept: every other route from the peer is accepted.
- `IOT-LP` has no route-filter; it sets local-preference 200 on every route that the export
  chain evaluates while the node is SRG1-active.
- Mist's `OrgOverlay_advertise` on the spokes has no final reject term.
- On the hub, `OVERLAY-IN` rejects only 10.255.0.0/16 and accepts every other spoke route
  (paper 4.5).

## 5. Mist native and Additional CLI at a glance

| Part | Mist native setting | Additional CLI |
|---|---|---|
| Tenant zones, WAN zone, `vpn_OrgOverlay` | yes (networks, WAN port name, VPN) | - |
| Zones `HA`, `ICD` | - | yes |
| `01_Internet`, `01_allow-to-hub` | yes (application policies) | IOT -> WAN `01_Internet` re-set below `GEO-BLOCK-DE` |
| `allow-ha`, `*-xnode`, `xnode-out`, `xnode-iot`, `GEO-BLOCK-DE` | - | yes |
| Tenant source NAT `<tenant>_to_wan[2]` | yes (Internet access on each network) | - |
| `ICD_to_wan` / `ICD_to_wan2` | - | yes |
| VR `lan` (tenant units, DHCP, overlay import) | yes | default next-table `WAN-VR`, delete `wan_default`, move GUEST out |
| `GUEST-VR`, `WAN-VR`, eBGP group `ICD`, rib-group `WAN-LEAK` and its policies | - | yes |
| Overlay IKE/IPsec, `st0.0`, `lo0.1`, iBGP `OrgOverlay_overlay` | yes (VPN path on the WAN port) | AS 65000, node-local, BFD, `IOT-LP`, DPD always-send |
| MNHA (`chassis high-availability`), SRG1 virtual IPs, signal routes | - | yes |

## 6. Changing or adding a tenant

A tenant's values sit in several places. Change all of them; the per-node items in both node
profiles:

| Item | Where |
|---|---|
| Network name, VLAN, subnet, gateway | `mist/org/networks.json`, and the `networks` copy in each node profile |
| Node address (.2 / .3) | `ip_configs` in each node profile |
| DHCP range, gateway, DNS | `dhcpd_config` in each node profile (GUEST: see below) |
| LAN trunk | `port_config` `ge-0/0/3` (`port_network` or `networks`) in each node profile, and the LAN switch |
| Internet and hub access | `service_policies` (`Internet`, `allow-to-hub`) and the network's `vpn_access` in each node profile |
| Gateway virtual IP | Additional CLI: `services-redundancy-group 1 virtual-ip <n>` (`ip`, `interface ge-0/0/3.<vlan>`, `use-virtual-mac`); the untagged network is `ge-0/0/3.0` |
| Cross-node return path | Additional CLI: the `WAN-VR` discard route (preference 250) and the `WAN-EXPORT` term `lan` route-filter |
| Cross-node egress | Additional CLI: the `<tenant>-xnode` policy to zone `ICD` |
| Routing instance | VR `lan` (Mist) or `GUEST-VR` (Additional CLI); the tenant's ISP follows its VR's default (section 4.6). The GUEST unit is also named in the Additional CLI: `set routing-instances GUEST-VR interface ge-0/0/3.30`, `delete groups top routing-instances lan interface ge-0/0/3.30` and the `GUEST-VR` DHCP group interface |
| GeoIP (if the tenant needs it) | Additional CLI: `GEO-BLOCK-DE` above the tenant's `-xnode` policy, `GEO-BLOCK-DE` on tenant -> WAN, and the re-set of the tenant's Mist `01_Internet` (paper 5.1) |
| Active Leasequery | Only when the peer address changes: the `lan` peer is on MGMT, the `GUEST-VR` peer on GUEST (paper 3.6, 5.5) |

Two rules from the paper:

- The GUEST DHCP group and pool are removed from Mist's render and set again in `GUEST-VR`
  with literal values. A change to the GUEST DHCP settings in a profile does not reach
  `GUEST-VR`: edit the `GUEST-VR` lines in both profiles (paper 5.5).
- The IOT `01_Internet` re-set lines carry Mist's generated names (`01_Internet`, address
  `10-10-60-0_24`). Copy them again from Mist's current render after any application-policy or
  network change, and check that `GEO-BLOCK-DE` is still sequence 1 (paper 5.1, 7).

## 7. Checks (paper 7)

```
show security zones
show security policies from-zone IOT to-zone ICD
show security policies from-zone ICD to-zone wan        (node 1; wan2 on node 2)
show bgp summary instance WAN-VR
show route receive-protocol bgp 10.255.2.2 table WAN-VR.inet.0 | no-more     (node 1)
show route receive-protocol bgp 10.255.2.1 table WAN-VR.inet.0 | no-more     (node 2)
show route 0.0.0.0/0 exact table lan.inet.0 | no-more
show route 0.0.0.0/0 exact table GUEST-VR.inet.0 | no-more
show route 10.255.3.1/32 exact
show bfd session
show security nat source rule all
```

Expected (paper 7): group `ICD` Established on both nodes; from the peer, 0/0 while the peer's ISP
is up and the hub-site prefixes while the peer's tunnel is up; the six tenant /24s arrive only on
the backup node, from the SRG1-active peer; the transit-link BFD session runs at 300 ms x 3;
10.255.3.1/32 is present only on the SRG1-active node.
