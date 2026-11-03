# Changes

## Release 1.0 (this repository, November 2026)

- `docs/SRX400-MNHA-Secure-Branch-Design.pdf`: the 2026-10-20 edition of the paper (29 pages),
  marked "public release 1.0" on page 1, with one new section, 10 "Reference configurations",
  which points to this repository. Other changes to the 20 Oct text:
  - 5.2 and 5.4: the lab's ATP Cloud region host and out-of-band management gateway are shown as
    the placeholders `<region>` and `<mgmt-gateway>`, as in 3.1, 3.5 and the configurations.
  - 5.4 and 9: the note on a production build with the WAN in inet.0 is reworded (three places).
  - Tenant networks: generic names, VLANs and subnets in the text, the CLI and the results: MGMT
    (VLAN 10, untagged), CORP (20), GUEST (30), MEDIA (40), SECURITY (50) and IOT (60), on
    10.10.10.0/24 to 10.10.60.0/24 (third octet = VLAN), with the `ge-0/0/3` units following the
    VLAN ids. Section 2 notes the change.
  - 3.6, 4.1, 4.2, 5.5, 7 and 9: notes on DHCP replies, what a Mist push keeps, removed Additional
    CLI lines, device-level Additional CLI lists, the Mist commit status and DHCP client routes are
    written as behavior statements and test results. In 4.1 and 4.2 they name the build they
    were seen on (Hub Profile build, section 2).
  - Page 1 header, 2, 3.6, 5.5, 6 and 9: the SRX400 release is named as
    Junos OS Evolved 25.4X300-D30.
  - 4.1, 5.1 and 8: Additional CLI accepts `#` comment lines as well as `set` and `delete` lines
    (Figure 4-6).
  - Contents: each section stays together in one column.
  - Mist screenshots: in Figures 4-1 to 4-6 the organization name is covered; in Figures 4-1
    and 4-2 the device MAC addresses, the SRX400 software versions and version status, and the
    management addresses are also covered.
  - Figures 4-4 to 4-6: new captures of a test copy of the published node 2 Hub Profile
    (`mist/hub-profiles/srx400-node2.json`) in a Mist test org, with the tenant plan of the text.
    Figure 4-5 shows all six tenants of the Internet policy and the steering path. In the test
    copy the VPN had another name (README, "Import test"); the path label in Figure 4-5 is shown
    with the published name `HUB-wan.OrgOverlay`. Figure 4-6 starts with the `#` header lines of
    the Additional CLI.
- Generic configurations of the 15 Oct 2026 Hub Profile build (paper sections 4 and 5), with the
  same tenant plan as the paper: Mist org objects, the three Hub Profiles with their Additional
  CLI, and the lab's as-built configuration of each device in display set form with the generic
  values substituted.
- `docs/zones-and-icd.md`: security zones, zone policies and the inter-node transit link on both
  nodes.
- `tools/mist_import.py` (creates the `mist/` objects through the Mist API); the `mist/` JSON files
  were import-tested through the Mist API (all six files) and through the Mist UI (the two node
  Hub Profiles); see README, "Import into Mist".

A later edition of the paper, with a section 4.6 on IPsec overlay design choices, is in review and
is not part of this release.

# Paper history

All dates are 2026. Section numbers refer to the version named in the heading.

## 2026-10-20 (29 pages)

The CLI in sections 4 and 5 now follows the as-built Additional CLI of the two SRX400 Hub Profiles
and the hub's Hub Profile (15 Oct build). Each result names the build and date it was tested on,
and a "Not yet tested" section lists what the results do not cover.

Added

- 3.10 LAN link failure behavior, and 6.5 LAN link failure on the active node: SRG1 monitors the
  LAN interface `ge-0/0/3`; timeline and packet-loss result.
- 5.4 Cross-node routing and policy (both nodes): `WAN-VR`, eBGP between the nodes over the
  inter-node transit link `ge-0/0/5` (AS 65001 / 65002, BFD 300 ms x 3), policies `WAN-EXPORT`,
  `ICD-IMPORT` and `HUB-FROM-OVERLAY`, rib-group `WAN-LEAK`, the tenant routing-instance defaults,
  `GUEST-VR`, zone `ICD` and the cross-node security policies. Former 5.4-5.6 are now 5.5-5.7.
- Section 9, Not yet tested.
- Section 2: a "Tested on" column and a description of each test build.
- Section 7: checks for LAN monitoring, MNHA configuration, session synchronization, transit-link
  BGP and routes, tenant egress, APBR, BFD, the signal route, GeoIP policy order, NAT rule hits,
  the Mist commit and manual failover.
- Section 8: step 0 (prerequisites in Mist and on the LAN switch). The order follows the Hub
  Profile build.

Changed

- 4.4: node 2's complete MNHA block - ICL address, MNHA forwarding path on the ICL, `lo0.0`
  forwarding addresses and static route, zone `HA`, LAN interface monitoring and all six SRG1
  virtual IPs - followed by node 1's differences.
- 4.5: the hub's Additional CLI (hub-site advertisement, `OVERLAY-IN` import filter, BGP BFD,
  DPD always-send).
- 4.3: node 2's full native settings (MGMT network, DHCP range, VPN access, steering paths,
  application policy names) and a table of tenant egress by routing instance.
- 4.1: a fuller split between what Mist renders and what is carried in Additional CLI; notes on
  what a Mist push keeps, set/delete-only Additional CLI, and confirming each commit on the box.
- 4.2: device-level Additional CLI lists.
- 3.4 and 5.3: as built, source NAT is interface NAT on both nodes, with rule-sets `ICD_to_wan`
  (node 1) and `ICD_to_wan2` (node 2). The NAT pool example was removed.
- 3.6 and 5.5: one Active Leasequery peer per DHCP routing instance (`lan` and `GUEST-VR`) with
  per-node peer addresses; `dhcp-local-server overrides no-unicast-replies` for 25.4X300-D30.2;
  manual failback procedure.
- 5.1: GeoIP policy order built with `set` and `delete` lines only (no `insert`), on the ICD path
  and on the WAN path.
- 5.6: the overlay as rendered by Mist (`vpn_OrgOverlay`, `OrgOverlay_overlay`,
  `OrgOverlay_advertise`) plus Additional CLI (AS 65000, node-local group, BGP BFD, `IOT-LP`
  local-preference, DPD always-send). This replaces the hand-written IKE, IPsec and BGP example.
- 5.7: static over IPsec marked LAB ONLY (not in the Hub Profiles).
- 3.2: fail-open behavior of the GeoIP object. 3.5: management-instance note for Mist-managed
  nodes. 3.7: what is and is not synchronized between the nodes.
- Topology: the link between the nodes on `ge-0/0/5` is labelled "transit link (eBGP)", zone
  `ICD`.
- Hub-site addressing: 10.200.0.0/16 with test host 10.200.8.1.
- Header names the SRX400 release. The subtitle no longer lists source NAT.

## 2026-10-16 (16 pages)

First version.
