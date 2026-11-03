# SRX400 MNHA secure branch under Juniper Mist - reference configurations

Generic reference configurations for an SRX400 Multinode High Availability (MNHA) hybrid pair
managed by Juniper Mist with **one Hub Profile per SRX400 node** (not a WAN Edge Template), plus
the vSRX overlay hub. They accompany the paper **"SRX400 MNHA Secure Branch Design"**
([docs/SRX400-MNHA-Secure-Branch-Design.pdf](docs/SRX400-MNHA-Secure-Branch-Design.pdf)) and match
its sections 4 and 5 (the Hub Profile build of 15 Oct 2026). This is a lab-built reference: paper
sections 2 and 6 list what was tested and on which build, and section 9 lists what was not.

Author: Eric Sandoval, Network Security Architect, HPE

Repository: https://github.com/SandmanJnpr/srx400-mnha-mist-branch

> **Disclaimer.** This reference was built and tested in the author's lab. It is not an official
> Juniper Networks or HPE position, design or support statement. Lines marked LAB ONLY belong to
> the lab, and the paper's section 9 lists what is not yet tested. Verify every line in your own
> lab before use.

## What the design covers

- SRX400 MNHA pair, hybrid mode, SRG1 active/backup with six tenant gateway virtual IPs.
- One ISP per node: ISP 1 on node 1, ISP 2 on node 2 (both on `ge-0/0/2`, DHCP).
- ICL on `ge-0/0/4` (MNHA control, session sync and the MNHA forwarding path).
- Inter-node transit link on `ge-0/0/5`: security zone `ICD`, eBGP between the nodes with BFD,
  per-tenant ISP steering with mutual backup through routing instances.
- Per-node interface source NAT; DHCP server on the SRG1-active node with Active Leasequery.
- Certificate-based IPsec overlay with iBGP from each node to a vSRX hub (Mist OrgOverlay VPN).
- GeoIP policy (ATP Cloud SecIntel feed) on the IOT tenant.

## Release

The SRX400 nodes were validated on Junos OS Evolved 25.4X300-D30; the vSRX hub runs
Junos OS 24.4R2-S4.12.

## Topology

```
                        vSRX-NG (overlay hub)  ge-0/0/0 172.16.11.2/30, gateway 172.16.11.1
                        (lab address, see "Replace with your values")
                        hub site 10.200.0.0/16 (LAB ONLY test host 10.200.8.1)
                                   |
                               Internet
                        /                    \
                    ISP 1                    ISP 2
                      |                        |
               ge-0/0/2 "wan"            ge-0/0/2 "wan2"
            +-----------------+        +-----------------+
            |    SRX400-1     |--------|    SRX400-2     |  ge-0/0/4  ICL 10.255.0.0/30 (zone HA)
            |  node 1, SRG1   |--------|  node 2, SRG1   |  ge-0/0/5  transit link 10.255.2.0/30
            |  priority 200   |        |  priority 100   |            (zone ICD, eBGP 65001-65002)
            +-----------------+        +-----------------+
               ge-0/0/3 trunk            ge-0/0/3 trunk
                         \                /
                  LAN switch: VLAN 10 untagged, VLANs 20, 30, 40, 50, 60 tagged

  Each node builds its own IPsec tunnel (st0.0) to the hub through its own ISP (node-local).
  re0:mgmt-0 on each node: out-of-band management (see Prerequisites).
```

| Tenant network (zone) | VLAN | `ge-0/0/3` unit | Subnet | Gateway (SRG1 VIP) | Node 1 / node 2 | Routing instance | Internet exit |
|---|---|---|---|---|---|---|---|
| MGMT | 10 (untagged) | 0 | 10.10.10.0/24 | 10.10.10.1 (virtual-ip 1) | .2 / .3 | `lan` | ISP 1 |
| CORP | 20 | 20 | 10.10.20.0/24 | 10.10.20.1 (virtual-ip 2) | .2 / .3 | `lan` | ISP 1 |
| GUEST | 30 | 30 | 10.10.30.0/24 | 10.10.30.1 (virtual-ip 3) | .2 / .3 | `GUEST-VR` | ISP 2 |
| MEDIA | 40 | 40 | 10.10.40.0/24 | 10.10.40.1 (virtual-ip 4) | .2 / .3 | `lan` | ISP 1 |
| SECURITY | 50 | 50 | 10.10.50.0/24 | 10.10.50.1 (virtual-ip 5) | .2 / .3 | `lan` | ISP 1 |
| IOT | 60 | 60 | 10.10.60.0/24 | 10.10.60.1 (virtual-ip 6) | .2 / .3 | `lan` (also on the overlay) | ISP 1 |

Each tenant's DHCP pool is .10 - .200 with router .1. The Active Leasequery peers are the other
node's address on MGMT (`lan`) and on GUEST (`GUEST-VR`).
MGMT is a LAN tenant (`ge-0/0/3.0`, VLAN 10 untagged). Out-of-band management is a separate
port, `re0:mgmt-0` (`<NODE1-MGMT-IP>`, `<NODE2-MGMT-IP>`).

| Item | Node 1 | Node 2 |
|---|---|---|
| MNHA local-id / SRG1 activeness-priority | 1 / 200 | 2 / 100 |
| ICL `ge-0/0/4` | 10.255.0.1/30 | 10.255.0.2/30 |
| MNHA forwarding address `lo0.0` | 10.255.1.1/32 | 10.255.1.2/32 |
| Mist router-id loopback, also on `lo0.0` (group `top`) | 100.100.0.1/32 | 100.100.0.2/32 |
| Transit link `ge-0/0/5` (zone `ICD`, `WAN-VR`) | 10.255.2.1/30, AS 65001 | 10.255.2.2/30, AS 65002 |
| SRG1 signal routes | active 10.255.3.1, backup 10.255.3.2 | same |
| WAN port name / zone / NAT | `wan` / `wan` / `<tenant>_to_wan`, `ICD_to_wan` | `wan2` / `wan2` / `<tenant>_to_wan2`, `ICD_to_wan2` |
| Overlay `st0.0` / `lo0.1` | 100.65.0.2/18 / 100.101.0.1 | 100.65.0.3/18 / 100.101.0.2 |

The overlay addresses (100.65.0.0/18, 100.101.0.x, 100.100.0.x) are assigned by Mist.

## Files

| File | What it is |
|---|---|
| `docs/SRX400-MNHA-Secure-Branch-Design.pdf` | The paper (20 Oct 2026 edition, public release 1.0, with section 10 pointing to this repository; see CHANGES.md) |
| `docs/zones-and-icd.md` | Security zones, zone policies and the transit link (zone `ICD`, eBGP in `WAN-VR`) on both nodes, quoting the configuration lines |
| `mist/org/networks.json` | The six org networks (MGMT, CORP, GUEST, MEDIA, SECURITY, IOT) |
| `mist/org/services.json` | The application `HUB-SITE-NETS` (10.200.0.0/16) used by the application policy `allow-to-hub` |
| `mist/org/vpns.json` | The hub-and-spoke VPN `OrgOverlay` with its path `HUB-wan` |
| `mist/hub-profiles/srx400-node1.json` | Hub Profile `SRX400-1` for SRX400 node 1 (native settings plus Additional CLI) |
| `mist/hub-profiles/srx400-node2.json` | Hub Profile `SRX400-2` for SRX400 node 2 |
| `mist/hub-profiles/vsrx-hub.json` | Hub Profile `HUB` for the vSRX hub `vSRX-NG` |
| `mist/additional-cli/*.txt` | The `additional_config_cmds` of each profile, one statement or `#` comment per line (the same lines as in the JSON) |
| `junos/srx400-node1.set`, `junos/srx400-node2.set`, `junos/vsrx-hub.set` | The lab's as-built configuration of each device in `display set` form (15 Oct 2026: Mist render of the lab's profiles + Additional CLI + the lines ATP Cloud enrollment writes), with the generic values substituted. Not a Mist render of the files in `mist/`. Adoption lines, secrets and the hub's lab-only lines are removed; the nodes' LAB ONLY lines remain. See "Notes on the configurations" for the derived lines |
| `tools/mist_import.py` | Creates the objects in `mist/` in a Mist org through the Mist API (Python 3, standard library only); see "Import into Mist" |

## How the files relate

```
mist/org/*.json            networks, application HUB-SITE-NETS, VPN OrgOverlay
        |  referenced by name
        v
mist/hub-profiles/*.json   native settings: WAN/LAN ports, per-node IPs, DHCP, VPN path,
        |                  traffic steering, application policies
        |  + additional_config_cmds  (= mist/additional-cli/*.txt)
        v
Mist render and commit on each device (once the profile is assigned to it)
        v
running configuration      compare with junos/*.set (the lab's as-built result, generic values)
```

- Mist renders the tenant zones, the WAN zone, `vpn_OrgOverlay`, the `01_Internet` and
  `01_allow-to-hub` policies, the per-tenant source NAT, VR `lan`, DHCP and the overlay
  (IKE/IPsec, `st0.0`, `lo0.1`, iBGP) from the profile's native settings.
- The Additional CLI adds MNHA, zones `HA` and `ICD`, `WAN-VR`, `GUEST-VR`, the eBGP between the
  nodes, the cross-node policies and NAT, overlay tuning, DHCP Active Leasequery, ATP Cloud /
  SecIntel and GeoIP, and removes Mist's APBR (`delete apply-groups apbr`).
- Each node profile also carries a copy of the six networks (key `networks`), as Mist returned it.
  Keep that copy identical to `mist/org/networks.json`.
- Each MNHA node is configured only by its own Hub Profile. The two nodes do not share a
  configuration.
- `docs/zones-and-icd.md` marks every quoted line as a Mist native setting or Additional CLI.
- The `junos/*.set` files are the lab's as-built result of the same build with the generic values
  substituted, not a Mist render of the files in `mist/`. In a Mist-managed build they are not
  loaded by hand; compare them with `show configuration | display set` on each device.

## Prerequisites

- The two SRX400 nodes and the vSRX hub claimed or adopted into one Mist org and connected, with
  the Mist subscriptions your org needs to manage WAN edges.
- **Out-of-band management with Internet access on each node.** These files place the WAN port
  `ge-0/0/2` in `WAN-VR`, and VR `lan` does not import Mist's inet.0 default. The only default in
  inet.0 is then the LAB ONLY `0.0.0.0/0 qualified-next-hop <mgmt-gateway> preference 1`, so the
  node reaches the Mist cloud, DNS, NTP and ATP Cloud only through `re0:mgmt-0` and
  `<mgmt-gateway>` (paper 3.5, 4.1, 5.4, 8 step 7). Before a profile is assigned, confirm that
  each node's management port reaches them. A node that reaches Mist only through its WAN port has
  no path to Mist after this profile commits. The two LAB ONLY items go together: do not remove
  the inet.0 default while the WAN sits in `WAN-VR`. The WAN-in-inet.0 variant is not tested
  (paper 5.4, 9).
- ATP Cloud: each chassis serial entitled (the lab used the premium tier) and a path from each
  node to ATP Cloud and DNS (paper 3.1, 8 step 7).
- A hub WAN address that both ISPs can reach (see "Replace with your values").
- On the LAN switch, VLAN 10 untagged and VLANs 20, 30, 40, 50 and 60 tagged on the trunk to
  `ge-0/0/3` of both nodes. The virtual IPs and both Active Leasequery peers need these VLANs on
  both nodes (paper 3.6, 8 step 0).

## Import into Mist

The JSON files in `mist/` are Mist API objects. Create them in this order: the org objects (the
six networks, the application `HUB-SITE-NETS` and the VPN `OrgOverlay`), then the Hub Profile
`HUB`, then the node Hub Profiles `SRX400-1` and `SRX400-2`. Creating a Hub Profile does not
assign it to a device; Mist configures a device from the Hub Profile assigned to it.

### Before you import

- Work on a copy of the repository and fill every placeholder in `mist/` (see "Placeholders").
  `tools/mist_import.py` refuses a file that still holds one (`--allow-placeholders` turns this
  check off; it is not meant for a real import). It does not check Additional CLI comment lines
  (lines that start with `#`), and `<*>` is Junos wildcard syntax, not a placeholder.
- Create the org networks, application and VPN before the Hub Profiles. The profiles reference
  them by name. The import test created them in this order, with every referenced object
  present; it did not create a profile whose references are missing.
- For the staged build of paper section 8 (see "Build order"), take the four blocks whose header
  starts with `# [after enrollment]` out of `additional_config_cmds` in both node files before
  the import (each block runs to the next `#` line, or to the end of the list): the ICD-path
  `GEO-BLOCK-DE` lines, the ATP Cloud / SecIntel lines, the GeoIP object with the WAN-path deny,
  and the `01_Internet` re-set.
- The VPN path name `HUB-wan` is built from the hub's Hub Profile name (`HUB`) and its WAN port
  name (`wan`). If you name the hub profile differently, change the path name in the VPN
  (`paths`), in the hub profile (`port_config` -> `vpn_paths`) and in both node profiles
  (`vpn_paths`, `path_preferences`).
- `tools/mist_import.py` stops when a name already exists in the org. If your org already holds
  an object of the same name (for example a VPN named `OrgOverlay`), rename the object in your
  copy and every reference to it. For the VPN these are: `name` in `mist/org/vpns.json`; the
  `vpn_access` key of IOT in `mist/org/networks.json` and in the `networks` copy of each node
  file; the `vpn_paths` keys (`HUB-wan.OrgOverlay`) of all three profiles; the path name in each
  node's `path_preferences`; and the Junos names that Mist renders from the VPN name and the
  Additional CLI uses (`vpn_OrgOverlay`, `vpn_OrgOverlay_bgp`, `OrgOverlay_overlay`,
  `OrgOverlay_advertise`, `OrgOverlay_hub_on_wan`). The traffic-steering name `OrgOverlay` (the
  `path_preferences` key) is a name inside the profile, not an org object. In the import test,
  each UI import also logged an update of the org VPN named `OrgOverlay` (the profile's
  traffic-steering name); its content did not change. The API import (`tools/mist_import.py`)
  logged no such update. Renaming the steering name was not tested.

### Option A: Mist UI

The import test used the Mist UI only for step 4, with the node profiles `SRX400-1` and
`SRX400-2`. It created the VPN, the application, the networks and `HUB` through the Mist API
(Option B); `--only org` of `tools/mist_import.py` is the tested way to create the org objects.

1. Create the VPN `OrgOverlay` with the values in `mist/org/vpns.json` (hub-and-spoke, path
   `HUB-wan`, BFD profile broadband).
2. Organization -> WAN -> Applications: create the application `HUB-SITE-NETS` with the values
   in `mist/org/services.json` (custom, 10.200.0.0/16, protocol any).
3. Organization -> WAN -> Networks: create the six networks with the values in
   `mist/org/networks.json` (name, VLAN ID, subnet, gateway, Internet access; for IOT also VPN
   access to `OrgOverlay`: routed, no re-advertise to the overlay). Objects created by hand in
   the UI can carry default fields that the files do not have; compare each network with the
   file (for example with a GET through the Mist API), as the `networks` copy in the node files
   must stay identical to it.
4. Organization -> WAN -> Hub Profiles -> Import Profile. The "Import Config" dialog asks for the
   JSON file and a Name. Choose `mist/hub-profiles/vsrx-hub.json`, type the Name `HUB` (the
   file's `name`), then Import. Import creates and saves the profile at once. Repeat with
   `mist/hub-profiles/srx400-node1.json` (Name `SRX400-1`) and
   `mist/hub-profiles/srx400-node2.json` (Name `SRX400-2`). The import test imported `HUB` through
   the API only.

### Option B: tools/mist_import.py

`tools/mist_import.py` creates the same objects through the Mist API: networks, application,
VPN, `HUB`, `SRX400-1`, `SRX400-2`. It only creates objects: it never changes an existing object
and never assigns a profile. Run it from the repository folder with an org API token that has
write access. In the commands, `<api-host>` is the API host of your Mist cloud (for example
`api.mist.com` or `api.eu.mist.com`) and `<org-id>` is your org ID. `read -rs` takes the token
without showing it and keeps it out of the shell history: paste the token, then press Return.

```
read -rs MIST_API_TOKEN && export MIST_API_TOKEN
python3 tools/mist_import.py --cloud <api-host> --org <org-id> --dry-run
python3 tools/mist_import.py --cloud <api-host> --org <org-id> --only org
python3 tools/mist_import.py --cloud <api-host> --org <org-id> --only hub
python3 tools/mist_import.py --cloud <api-host> --org <org-id> --only nodes
```

- `--dry-run` writes nothing. With the token set it reads the org: it lists the objects it would
  create, warns when a profile references a network, application or VPN that is neither in the
  org nor in the run, and stops when a name already exists in the org. It also stops on a
  placeholder, or on a name outside the Mist name rule (1-32 letters, digits, `_` or `-`,
  starting and ending with a letter or digit). The reference warning covers the network names in
  `ip_configs`, `dhcpd_config`, `port_config` and `service_policies`, the application names in
  `service_policies` and the VPN name in the `vpn_paths` keys. It does not check the path name
  (`HUB-wan`), the `path_preferences` path names or the IOT `vpn_access` key.
- `--only org` creates the networks, the application and the VPN; `--only hub` the Hub Profile
  `HUB`; `--only nodes` the Hub Profiles `SRX400-1` and `SRX400-2`. Without `--only` it creates
  all of them, in that order.
- Each run adds the IDs of the objects it created to `mist_import_manifest.json` in the current
  folder (`--manifest FILE` to choose another file). The manifest holds your Mist API host, org
  ID and object IDs; the repository's `.gitignore` excludes `mist_import_manifest.json` and
  `*.tmp`. To remove those objects again, list them, then delete them:

  ```
  python3 tools/mist_import.py --cloud <api-host> --org <org-id> --delete-created mist_import_manifest.json --dry-run
  python3 tools/mist_import.py --cloud <api-host> --org <org-id> --delete-created mist_import_manifest.json
  ```

  It deletes only the objects listed in that manifest, newest first, and only an object that
  still carries the name in the manifest. It does not check whether a profile is assigned:
  unassign a profile from its device before you delete it.
- `--prefix X` puts X in front of the name of every Hub Profile in the run, `HUB` included when
  `HUB` is in the run (`--only hub`, `--only all` or no `--only`). The VPN path name follows the hub profile's
  name (see "Before you import") and `--prefix` does not change the path names, so use `--prefix`
  only with `--only nodes`, for a test import next to existing profiles. The import test used it
  that way only.
- `--skip-existing` uses an existing object of the same name as it is, without comparing it with
  the file; check that each existing object matches the file.
- `--dir PATH` reads `mist/` from another folder (default: this repository).

### Assign the profiles

Assign each Hub Profile to its own device: `HUB` to the vSRX hub, `SRX400-1` to node 1 and
`SRX400-2` to node 2, at the steps of "Build order" below. After every assignment or change,
confirm the Mist commit on the device (`show system commit`).

### Import test

The files were import-tested on 3 Nov 2026 in a Mist test org; no profile was assigned to a
device or site. The tested copy differed from the published files in two ways:

- Every placeholder was filled with a documentation value (`tools/mist_import.py` refused the
  files as published). Additional CLI comment lines and `<*>` were left as published.
- The org already held a VPN named `OrgOverlay`, so the VPN was created under a test name. The
  name was changed in `mist/org/vpns.json`, in the IOT `vpn_access` key (org networks and the
  `networks` copy of each node file), in the `vpn_paths` keys and in the `path_preferences` path
  names. The traffic-steering name `OrgOverlay` (a name inside the profile) and the Additional
  CLI were not changed; no profile was assigned, so Mist rendered no configuration from them.

Results:

- `tools/mist_import.py` created the networks, the application `HUB-SITE-NETS`, the VPN and the
  Hub Profile `HUB`, and the node Hub Profiles from `srx400-node1.json` and `srx400-node2.json`
  with `--prefix` (under a test name). `SRX400-1` and `SRX400-2` were imported through the Mist
  UI (Organization -> WAN -> Hub Profiles -> Import Profile, which asks for the JSON file and a
  Name).
- Each created object was read back through the Mist API and compared field for field with its
  file in the tested copy. Apart from the changes in the next item, no field was dropped, added
  or changed, list order and nested key order were kept, and the Additional CLI came back line
  for line (259 lines per node profile, 23 for the hub). The UI import and the API import stored
  the same profile.
- On import Mist adds its own `id`, `org_id`, `created_time` and `modified_time`, adds
  `"zone_id": null` to each network, and moves the top-level `name` (and `type`) keys to the end
  of each object.
- `--delete-created` then deleted every created object; each one read back as not found.
- The `junos/*.set` files are the lab's as-built running configurations with the generic values
  substituted. They are not a new Mist render of the generic profiles: no device was assigned a
  profile in the import test.

## Build order (condensed from paper section 8)

1. **Org objects** (paper 8 step 0). Create the networks, the application and the VPN from
   `mist/org/` ("Import into Mist").
2. **Hub** (paper 8 step 0, 4.5). Import the Hub Profile `HUB` from
   `mist/hub-profiles/vsrx-hub.json`, assign it to the hub and confirm that the hub is connected
   and its commit is on the box (`show system commit`).
3. **LAN switch** (paper 8 step 0). Carry the tenant VLANs to both nodes as listed under
   Prerequisites.
4. **Node profiles, first import** (paper 8 steps 1-6). Import `SRX400-1` and `SRX400-2` from
   `mist/hub-profiles/srx400-node1.json` and `srx400-node2.json` without the four
   `# [after enrollment]` blocks ("Before you import"). Assign each profile to its own device.
   Keep the Additional CLI in the profile: a device-level Additional CLI list replaces the
   profile's list. After every change, confirm the Mist commit on the node
   (`show system commit`).
5. **D30.2 DHCP replies** (paper 5.5, 8 step 6). The paper requires
   `set routing-instances lan system services dhcp-local-server overrides no-unicast-replies` and
   `set routing-instances GUEST-VR system services dhcp-local-server overrides no-unicast-replies`
   on 25.4X300-D30.2, on both nodes. They are not in the 15 Oct profiles, so they are not in these
   files. Add both lines to both node profiles at the end of the DHCP block, after the last
   `set system processes dhcp-service` line. Pushing them from the profiles, and the `GUEST-VR`
   line by any method, is not yet tested (paper 3.6, 5.5, 9).
6. **Check** the MNHA, transit link, overlay and DHCP rows of the paper's section 7 checklist.
7. **ATP Cloud** (paper 8 steps 7-8). Enroll each node with the command from the ATP Cloud portal
   (paper 3.1). Then add the ATP Cloud / SecIntel block back to each profile, in the same place in
   the list; it references the certificates and CA profiles that enrollment creates. Check the
   cloud connection and feed refresh rows.
8. **GeoIP** (paper 8 step 9). Add the three GeoIP blocks back in their places: the ICD-path
   `GEO-BLOCK-DE` lines directly above the `IOT-xnode` lines (not at the end of the list), the
   GeoIP object with the WAN-path deny, then the `01_Internet` re-set. Copy the re-set lines from
   Mist's current render of each node (paper 5.1). Check that `GEO-BLOCK-DE` is sequence 1 on
   IOT -> ICD and on IOT -> wan (node 1) or wan2 (node 2).
9. **Test and fail over** as in paper 8 step 10.

Building a new or replacement node from its profile is the untested "Fresh node build" item of
paper section 9, including a push of the enrollment lines (paper 5.2) before the node is enrolled.

## Placeholders

Replace every placeholder before the import. A placeholder left in a native field is not a valid
value, and one left in the Additional CLI produces a configuration that does not commit on the
node. `tools/mist_import.py` refuses to import a file in `mist/` that still holds a placeholder
(the first four rows; the last four rows occur only in `junos/*.set`), unless it is run with
`--allow-placeholders`.

| Placeholder | Where | Replace with |
|---|---|---|
| `<NODE1-MGMT-IP>`, `<NODE2-MGMT-IP>`, `<HUB-MGMT-IP>` | `oob_ip_config.ip` in the Hub Profile JSON; `re0:mgmt-0` / `fxp0` in `junos/*.set` | The out-of-band management address of each device (the JSON keeps `"netmask": "/24"`) |
| `<mgmt-gateway>` | `oob_ip_config.gateway`; the LAB ONLY inet.0 default in the node Additional CLI and `junos/*.set` | The out-of-band management gateway |
| `<hub-MAC>` | The two DPD lines in each node's Additional CLI; the IKE gateway and IPsec VPN names in `junos/srx400-node*.set` | The hub's MAC address as 12 lowercase hex digits with no separators, as Mist shows it for the hub device. Mist builds the IKE gateway name as `<node WAN port name>_to_<hub-MAC>_<hub WAN port name>`: `wan_to_<hub-MAC>_wan` on node 1, `wan2_to_<hub-MAC>_wan` on node 2 (paper 5.6). After the first render, confirm the name with `show configuration security ike` on each node |
| `<region>` | ATP Cloud connection URL in the node Additional CLI and `junos/srx400-node*.set` | The region host of your ATP Cloud realm, as written by enrollment (the same region as in the enrollment URL, paper 3.1) |
| `<ROOT-PASSWORD-HASH>` | `junos/*.set` only | Set by you or by Mist; never stored in these files |
| `<NTP-SERVER>` | `junos/*.set` only | Mist renders the NTP server it uses (the node profiles set `pool.ntp.org`) |
| `<cloud>` | `junos/*.set` only (Mist address-book entries, policy `allow_mist`, the hub's log stream host) | Mist renders the host names of your Mist cloud |
| `<ORG-ID>` | `junos/vsrx-hub.set` only (IKE dynamic distinguished-name wildcard) | Mist renders your org ID |

`<*>` in `set groups MNHA-NODE-LOCAL security ike gateway <*> node-local` is Junos wildcard
syntax, not a placeholder. Keep it as it is (paper 4.4, 5.6).

## Replace with your values

| Value in these files | Where | Replace with |
|---|---|---|
| Hub WAN `172.16.11.2/30`, gateway `172.16.11.1` | `mist/hub-profiles/vsrx-hub.json` (`port_config` `ge-0/0/0`); rendered as the IKE gateway address on both nodes | An address both ISPs can reach. In the lab, both ISPs reach this address through lab routing and a second ISP-side link on the hub that are not in these files (paper 4.5) |
| Hub site `10.200.0.0/16` | `mist/org/services.json`; node `HUB-FROM-OVERLAY` and `ICD-IMPORT` route-filters; hub Additional CLI | Your hub-site prefixes (see LAB ONLY for the hub's discard route) |

## Names in these files and in the paper

| Paper text or figure | These files |
|---|---|
| "SRX400 node 1", "SRX400 node 2" (device labels) | Mist device names and host names `SRX400-1`, `SRX400-2` |
| "vSRX-NG" | `vSRX-NG` (host name rendered from the Mist device name) |
| "node 1 profile", "node 2 profile", "vSRX hub profile" | Hub Profiles `SRX400-1`, `SRX400-2`, `HUB` (Mist API names allow letters, digits, `_` and `-` only) |
| Hub overlay path "HUB-wan" (Figure 4-3) and steering path "HUB-wan.OrgOverlay" (Figure 4-5) | VPN path `HUB-wan`; `HUB-wan.OrgOverlay` in `vpn_paths` and `path_preferences` |

## LAB ONLY (paper sections in brackets)

- `WAN-VR` holds the WAN port `ge-0/0/2` together with the transit link `ge-0/0/5`, so that inet.0
  keeps the out-of-band management default (4.3, 5.4). The paper notes that a production build
  keeps the WAN in inet.0; that variant is not tested (9).
- The inet.0 default `0.0.0.0/0 qualified-next-hop <mgmt-gateway> preference 1` toward the
  out-of-band management gateway (4.1, 5.4). It goes together with the item above (see
  Prerequisites).
- The hub-site test host 10.200.8.1/32 on the hub's `lo0.1`, and the hub site itself as a
  10.200.0.0/16 discard route (4.5). The discard route is the only source of the hub-site
  advertisement, and term `10_hub_site` of `OrgOverlay_advertise` matches static routes and the
  exact /16 only. Replace the discard route with your real hub-site routes and set the term's
  `from protocol` and route-filter to match them.
- In the lab, ATP Cloud enrollment, the cloud connection, DNS and feed refresh used the
  out-of-band management network (3.5, 8).
- Not in these files: the on-box test lines of 3.5 (SecIntel over `fxp0`), 5.7 (static over IPsec)
  and 6.1 (on-box GeoIP policies and a temporary NAT pool).

Zone `vpn_OrgOverlay` (Mist native) and zones `HA` and `ICD` accept all host-inbound services; set
your own management access policy.

## Design limits (from the paper)

- GUEST crosses the transit link in steady state (node 1 active). After a failover to node 2,
  the five `lan` tenants cross it instead (3.4, 4.3).
- Firewall sessions are synchronized between the nodes; IPsec security associations are not
  (each tunnel is node-local); DHCP bindings reach the peer only through Active Leasequery
  (3.6, 3.7).
- The zone pair and NAT point of a `lan` tenant's Internet session differ by active node (9).
- GeoIP fails open: while the feed is empty or not yet downloaded, the deny policy blocks nothing
  (3.2).
- No fail-closed route covers 10.200.0.0/16. With both tunnels down, hub-site traffic follows the
  tenant's default route, that is, out of an ISP outside IPsec (9).
- Nothing tracks the upstream ISP path: `WAN-EXPORT` advertises the default whenever the node has
  a DHCP default (5.4, 9).
- Only `ge-0/0/3` moves SRG1; the transit link `ge-0/0/5` is not monitored (9).
- No activeness-probe and no preemption are configured; failback is manual; ICL loss and
  split-brain are not tested (4.4, 9).
- The cross-node policies match any source, destination and application, and zone `ICD` accepts
  all host-inbound services and protocols (5.4, 9).
- Several routing policies end open (`ICD-IMPORT` ends with accept, the spokes have no overlay
  import policy); see `docs/zones-and-icd.md`, "Policy limits" (9).

## Not yet tested (paper section 9)

GeoIP from the Hub Profiles; DHCP on the Hub Profile build; DHCP client routes after failover;
transit link exposure; ICL loss and split-brain; active node power-off or reboot; established
sessions; upstream ISP failure; transit link failure; hub down; export and import policy
hardening; static over IPsec; Internet egress as built (no tenant traffic has used the as-built
interface NAT or left by ISP 2); source NAT pool; ATP Cloud / SecIntel over the data plane; WAN in
inet.0; device-level Additional CLI; fresh node build. The GeoIP lines in the
profiles were added after the 6.1 test (paper 5.1). Section 9 of the paper describes each item.

## What these files leave out

- The lines Mist writes at adoption: the `mist` login user and its keys, the outbound-ssh
  connection to the Mist cloud (device-id and secret), group `mist-script`, scripts, extensions
  and the ephemeral configuration database.
- Certificates and keys. The Mist overlay certificates (`mist-vpn-cert-1`, CA profile
  `mist-vpn-ca`) and the ATP Cloud certificates are referenced by name only.
- DHCP host reservations; the pools keep their .10 - .200 ranges.
- Management access settings (SSH root login, SFTP server, ping on the hub's WAN zone,
  `commit synchronize`).
- The hub's lab-only lines (management, lab routes, a second ISP-side link and a local test zone;
  paper 4.5), a lab CA profile on the nodes, box-local lines (factory CA profiles and the
  application-identification download schedule on the hub, and a bare
  `set services application-identification` line on node 2), and the comment lines and clean-up
  delete lines of the Additional CLI that the design does not need. Short section headers (lines
  starting with `#`) take the place of the comments.
- The `set version` line of `junos/srx400-node1.set` and `junos/srx400-node2.set`. "Release"
  above and the header of each file name the release.
- In the lab, node 2 also carried a device-level Additional CLI list identical to its profile's
  list (paper 4.2). These files keep one copy, in the profile.

## Notes on the configurations and the paper

- The configurations are the 15 Oct 2026 Hub Profile build that sections 4 and 5 describe, with
  the paper's names and addresses and the generic tenant plan (paper 2).
- In `junos/srx400-node*.set`, the per-tenant blocks that the lab capture listed in the order of
  the network names (zones, `same_zone` policies, tenant source NAT, `allow_mist`, the DHCP groups,
  pools and interfaces of VR `lan`) are listed in the order of the generic names: CORP, GUEST,
  IOT, MEDIA, MGMT, SECURITY. The `WAN-VR` tenant discard routes are listed in prefix order
  (10.10.10.0/24 to 10.10.60.0/24), as Junos lists static routes. Only the order of these blocks
  changes; other blocks keep the captured order.
- Derived lines, not captured from a Mist render: the lab application listed several hub-site
  prefixes, which these files show as the paper's one aggregate 10.200.0.0/16. On the nodes, the
  address-book entry `10-200-0-0_16` and the two `destination-address 10-200-0-0_16` lines
  (policy `01_allow-to-hub`, group `apbr`) follow Mist's naming for that application; on the hub,
  the 10.200.0.0/16 discard route and the `10_hub_site` route-filter; in `mist/org/services.json`,
  the one address of `HUB-SITE-NETS`. Render a profile with your own application to confirm the
  names.
- The `junos/srx400-node*.set` files also hold lines that no profile carries: the `aamw-ca`,
  `aamw-secintel-ca` and `aamw-cloud-ca` CA profiles, written by ATP Cloud enrollment (paper 4.1).
- `oob_ip_config` in the node profiles carries `"node1": {"type": "dhcp"}` as Mist returned it.
  That key is Mist's setting for the second node of a chassis cluster; it is unused in MNHA, where
  each node has its own profile.
- Paper 4.5 describes "a multipoint `st0` per path"; for the one overlay path in the lab, Mist
  rendered four multipoint units on the hub (`st0.0` - `st0.3`, see `junos/vsrx-hub.set`).
- Paper 5.6 mentions the master-instance AS line in a note only; the profiles carry
  `set routing-options autonomous-system 65001` (node 1) and `65002` (node 2).
- The interface description of `ge-0/0/5` reads "inter-node transit link to SRX400-x" (x = the
  peer node). Its security zone and BGP group are named `ICD`; it is not the MNHA ICD (see
  `docs/zones-and-icd.md`).
- GeoIP policy order depends on the order of the Additional CLI lines: the IOT -> ICD
  `GEO-BLOCK-DE` lines come before `IOT-xnode`, and Mist's IOT `01_Internet` is deleted and
  set again after `GEO-BLOCK-DE` (paper 5.1, 8). Keep the line order when you edit the lists.
- To change or add a tenant, see `docs/zones-and-icd.md`, "Changing or adding a tenant".

Juniper, Junos, Mist and SRX are trademarks of Juniper Networks, Inc.
