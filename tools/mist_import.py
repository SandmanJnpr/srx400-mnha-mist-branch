#!/usr/bin/env python3
"""Create the mist/ objects of this repository in a Mist org through the Mist API.

Usage:
  export MIST_API_TOKEN=<org API token with write access>
  python3 tools/mist_import.py --cloud api.<region>.mist.com --org <ORG_ID> [--only org|hub|nodes|all]
        [--prefix X] [--dir PATH] [--manifest FILE] [--skip-existing] [--allow-placeholders] [--dry-run]
  python3 tools/mist_import.py --cloud api.<region>.mist.com --org <ORG_ID> --delete-created FILE [--dry-run]

Order: networks -> services -> vpns (mist/org/*.json) -> Hub Profile HUB (mist/hub-profiles/vsrx-hub.json)
-> node Hub Profiles SRX400-1, SRX400-2 (mist/hub-profiles/srx400-node1.json, srx400-node2.json).
  --only org|hub|nodes|all  which part to create (default all)
  --prefix X                prepend X to the Hub Profile names (for a test import next to existing
                            profiles). Org objects and the references to them keep their names.
  --dir PATH                folder that holds mist/ (default: this repository)
  --manifest FILE           where the ids of created objects are written (default mist_import_manifest.json);
                            an existing manifest for the same org is appended to
  --skip-existing           skip an object whose name already exists in the org (default: stop before
                            creating anything). An existing object is never changed.
  --allow-placeholders      import even if a value still holds a <...> placeholder (README, Placeholders)
  --dry-run                 print what would be done; no writes (read-only GETs if a token is set)
  --delete-created FILE     delete the objects listed in a manifest written by this script, newest first

The script only creates (POST) objects and only deletes objects listed in its own manifest. It never
assigns a profile to a device or a site. Create the org objects first. The script warns when a profile
references a network, application or VPN that does not exist in the org.
Standard library only.
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.request

# README "Placeholders". Lines that start with '#' (comments in additional_config_cmds) are not checked;
# <*> is Junos wildcard syntax, not a placeholder.
PLACEHOLDERS = {
    "<NODE1-MGMT-IP>": "out-of-band management address of SRX400 node 1 (oob_ip_config.ip)",
    "<NODE2-MGMT-IP>": "out-of-band management address of SRX400 node 2 (oob_ip_config.ip)",
    "<HUB-MGMT-IP>": "out-of-band management address of the vSRX hub (oob_ip_config.ip)",
    "<mgmt-gateway>": "out-of-band management gateway (oob_ip_config.gateway, node inet.0 default)",
    "<hub-MAC>": "hub MAC, 12 lowercase hex digits, no separators (node DPD lines)",
    "<region>": "ATP Cloud region host (node ATP Cloud connection URL)",
    "<ROOT-PASSWORD-HASH>": "junos/*.set only", "<NTP-SERVER>": "junos/*.set only",
    "<cloud>": "junos/*.set only", "<ORG-ID>": "junos/vsrx-hub.set only",
}
PH_RE = re.compile(r"<[A-Za-z][A-Za-z0-9_-]*>")
NAME_RE = re.compile(r"[A-Za-z0-9]([A-Za-z0-9_-]{0,30}[A-Za-z0-9])?")  # Mist UI rule, max 32
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
CLOUD_RE = re.compile(r"api(\.[a-z0-9-]+)*\.mist\.com")
SERVER_KEYS = ("id", "org_id", "created_time", "modified_time")
ORG_FILES = [("networks", "mist/org/networks.json"), ("services", "mist/org/services.json"),
             ("vpns", "mist/org/vpns.json")]
HUB_FILE = "mist/hub-profiles/vsrx-hub.json"
NODE_FILES = ["mist/hub-profiles/srx400-node1.json", "mist/hub-profiles/srx400-node2.json"]


class Mist:
    def __init__(self, cloud, org, token):
        self.base, self.org, self.token = "https://%s/api/v1/orgs/%s" % (cloud, org), org, token

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={
            "Authorization": "Token " + self.token, "Accept": "application/json",
            "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    raw = r.read()
                    return r.status, (json.loads(raw) if raw else None)
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", "replace")
                if e.code == 429 and attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                return e.code, raw

    def names(self, kind):
        query = "?type=gateway&limit=1000" if kind == "deviceprofiles" else "?limit=1000"
        code, body = self.call("GET", "/%s%s" % (kind, query))
        if code != 200 or not isinstance(body, list):
            sys.exit("GET %s failed: %s %s" % (kind, code, body))
        return {o.get("name", "").lower() for o in body}


def load(root, rel):
    with open(os.path.join(root, rel)) as f:
        return json.load(f)


def placeholders(obj, where, found):
    if isinstance(obj, dict):
        for k, v in obj.items():
            placeholders(v, "%s.%s" % (where, k), found)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            placeholders(v, "%s[%d]" % (where, i), found)
    elif isinstance(obj, str) and not obj.lstrip().startswith("#"):
        for p in PH_RE.findall(obj):
            found.append((where, p))


def refs(profile):
    """Org object names a Hub Profile references: (networks, services, vpns)."""
    nets, svcs, vpns = set(profile.get("ip_configs", {})), set(), set()
    nets |= {k for k in profile.get("dhcpd_config", {}) if k != "enabled"}
    for pc in profile.get("port_config", {}).values():
        nets |= set(pc.get("networks", [])) | ({pc["port_network"]} if pc.get("port_network") else set())
        vpns |= {k.rpartition(".")[2] for k in pc.get("vpn_paths", {})}
    for sp in profile.get("service_policies", []):
        nets |= set(sp.get("tenants", []))
        svcs |= {s for s in sp.get("services", []) if s != "any"}
    return nets, svcs, vpns


def write_manifest(path, man):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(man, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def delete_created(api, args):
    with open(args.delete_created) as f:
        man = json.load(f)
    if man.get("cloud") != args.cloud or man.get("org_id") != args.org:
        sys.exit("manifest is for another cloud or org; nothing deleted")
    for item in list(reversed(man["created"])):
        what = "%s %s" % (item["type"], item["name"])
        if args.dry_run:
            print("would delete", what)
            continue
        code, body = api.call("GET", "/%s/%s" % (item["type"], item["id"]))
        name = body.get("name") if isinstance(body, dict) else None
        if code == 404:
            print("already gone", what)
        elif code != 200 or name != item["name"]:
            print("NOT deleted %s: GET returned %s, name %r" % (what, code, name))
            continue
        else:
            code, body = api.call("DELETE", "/%s/%s" % (item["type"], item["id"]))
            gone = api.call("GET", "/%s/%s" % (item["type"], item["id"]))[0] == 404
            print("deleted" if code == 200 and gone else "DELETE FAILED (%s) %s" % (code, body), what)
            if not (code == 200 and gone):
                continue
        man["created"].remove(item)
        write_manifest(args.delete_created, man)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cloud", required=True, help="api.<region>.mist.com, e.g. api.mist.com, api.eu.mist.com")
    ap.add_argument("--org", required=True, help="Mist org ID")
    ap.add_argument("--only", choices=["org", "hub", "nodes", "all"], default="all")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--manifest", default="mist_import_manifest.json")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--allow-placeholders", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--delete-created", metavar="MANIFEST")
    args = ap.parse_args()
    args.cloud = args.cloud.replace("https://", "").strip("/")
    if not CLOUD_RE.fullmatch(args.cloud) or not UUID_RE.fullmatch(args.org):
        sys.exit("--cloud must be api[.<region>].mist.com and --org a Mist org ID")
    token = os.environ.get("MIST_API_TOKEN", "").strip()
    if not token and not args.dry_run:
        sys.exit("set MIST_API_TOKEN")
    api = Mist(args.cloud, args.org, token) if token else None
    if args.delete_created:
        if not api:
            sys.exit("set MIST_API_TOKEN")
        return delete_created(api, args)

    plan = []  # (kind, rel file, body)
    if args.only in ("org", "all"):
        for kind, rel in ORG_FILES:
            plan += [(kind, rel, o) for o in load(args.dir, rel)]
    for rel in ([HUB_FILE] if args.only in ("hub", "all") else []) + \
               (NODE_FILES if args.only in ("nodes", "all") else []):
        prof = dict(load(args.dir, rel))
        prof["name"] = args.prefix + prof["name"]
        plan.append(("deviceprofiles", rel, prof))
    plan = [(k, r, {x: v for x, v in b.items() if x not in SERVER_KEYS}) for k, r, b in plan]

    errors, found = [], []
    for kind, rel, body in plan:
        if not NAME_RE.fullmatch(body.get("name", "")):
            errors.append("%s %r: name must be 1-32 letters, digits, _ or -, starting and ending "
                          "with a letter or digit" % (kind, body.get("name")))
        placeholders(body, "%s:%s" % (rel, body.get("name")), found)
    for where, p in found:
        print("placeholder %s in %s -> %s" % (p, where, PLACEHOLDERS.get(p, "replace it (README, Placeholders)")))
    if found and not args.allow_placeholders:
        errors.append("%d placeholder value(s) left; replace them or pass --allow-placeholders" % len(found))
    if errors:
        sys.exit("\n".join(["refused, nothing created:"] + errors))

    existing = {k: api.names(k) for k in ("networks", "services", "vpns", "deviceprofiles")} if api else None
    if existing:
        planned = {k: {b["name"].lower() for kk, _, b in plan if kk == k} for k in existing}
        for kind, rel, body in plan:
            if kind != "deviceprofiles":
                continue
            for k, names in zip(("networks", "services", "vpns"), refs(body)):
                for n in sorted(names):
                    if n.lower() not in existing[k] | planned[k]:
                        print("warning: %s %s references %s %r, which is not in the org" % (kind, body["name"], k, n))
        clash = [(k, b["name"]) for k, _, b in plan if b["name"].lower() in existing[k]]
        for k, n in clash:
            print("exists in the org: %s %s%s" % (k, n, " (skipped, the existing object is used as is)"
                                                  if args.skip_existing else ""))
        if clash and not args.skip_existing:
            sys.exit("refused, nothing created: %d name(s) already exist; rename them in your copy, "
                     "use --prefix for the profiles, or --skip-existing" % len(clash))
        plan = [p for p in plan if p[2]["name"].lower() not in existing[p[0]]]
    if args.dry_run:
        print("dry run%s:" % ("" if existing else " (no token, org not checked)"))
        for kind, rel, body in plan:
            print("  would create %s %s  (from %s)" % (kind, body["name"], rel))
        return 0

    man = {"cloud": args.cloud, "org_id": args.org, "created": []}
    if os.path.exists(args.manifest):
        with open(args.manifest) as f:
            man = json.load(f)
        if man.get("cloud") != args.cloud or man.get("org_id") != args.org:
            sys.exit("%s belongs to another cloud or org; use another --manifest" % args.manifest)
    for kind, rel, body in plan:
        code, res = api.call("POST", "/" + kind, body)
        if code != 200 or not isinstance(res, dict) or "id" not in res:
            sys.exit("POST %s %s failed: %s %s\nstopped; created so far: %s" % (
                kind, body["name"], code, res, args.manifest))
        man["created"].append({"type": kind, "name": res.get("name"), "id": res["id"], "file": rel,
                               "created_time": res.get("created_time")})
        write_manifest(args.manifest, man)
        print("created %s %s" % (kind, res.get("name")))
    print("manifest: %s (%d object(s)); clean up with --delete-created %s" % (
        args.manifest, len(man["created"]), args.manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
