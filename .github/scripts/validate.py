#!/usr/bin/env python3
"""Sanity checks for this Umbrel community app store.

Run from the repository root: python3 .github/scripts/validate.py
"""

import glob
import os
import re
import sys

import yaml

errors = []


def error(message):
    errors.append(message)
    print("ERROR: " + message)


def load(path):
    try:
        with open(path) as handle:
            return yaml.safe_load(handle)
    except Exception as exc:  # report every broken file, not just the first
        error(path + ": invalid YAML: " + str(exc))
        return None


# Every YAML file must parse.
for path in sorted(glob.glob("**/*.y*ml", recursive=True) + glob.glob(".github/**/*.y*ml", recursive=True)):
    if path.endswith((".yml", ".yaml")):
        load(path)

store = load("umbrel-app-store.yml") or {}
store_id = store.get("id", "")
if not re.fullmatch(r"[a-z-]+", str(store_id)):
    error("umbrel-app-store.yml: id must contain only a-z and dashes")

REQUIRED = [
    "manifestVersion", "id", "name", "tagline", "category", "version", "port",
    "description", "website", "support", "gallery",
]
IMAGE_PINNED = re.compile(r"^[^\s:@]+(/[^\s:@]+)*:[^\s@]+@sha256:[0-9a-f]{64}$")
ports = {}

app_dirs = sorted(os.path.dirname(p) for p in glob.glob("*/umbrel-app.yml"))
if not app_dirs:
    error("no apps found")

for app_dir in app_dirs:
    manifest = load(os.path.join(app_dir, "umbrel-app.yml")) or {}
    app_id = manifest.get("id")
    for field in REQUIRED:
        if field not in manifest:
            error(app_dir + "/umbrel-app.yml: missing '" + field + "'")
    if app_id != app_dir:
        error(app_dir + ": manifest id '" + str(app_id) + "' must equal the folder name")
    if not str(app_id).startswith(store_id + "-"):
        error(app_dir + ": app id must start with the store id '" + store_id + "-'")
    if not isinstance(manifest.get("version"), str):
        error(app_dir + ": version must be a quoted string")
    port = manifest.get("port")
    if not isinstance(port, int) or port in (80, 443, 2000) or 40000 <= port <= 49999:
        error(app_dir + ": invalid or reserved port " + str(port))
    elif port in ports:
        error(app_dir + ": port " + str(port) + " already used by " + ports[port])
    else:
        ports[port] = app_dir
    if manifest.get("storage") not in (None, {"dataRoot": "data"}):
        error(app_dir + ": storage must be exactly {dataRoot: data}")

    compose = load(os.path.join(app_dir, "docker-compose.yml")) or {}
    services = compose.get("services") or {}
    proxy = (services.get("app_proxy") or {}).get("environment") or {}
    app_host = str(proxy.get("APP_HOST", ""))
    if not app_host.startswith(str(app_id) + "_") or not app_host.endswith("_1"):
        error(app_dir + ": APP_HOST must be '<app-id>_<service>_1', got '" + app_host + "'")
    elif app_host[len(str(app_id)) + 1:-2] not in services:
        error(app_dir + ": APP_HOST points at a service that does not exist")
    for name, service in services.items():
        if name == "app_proxy":
            continue
        image = str((service or {}).get("image", ""))
        if not IMAGE_PINNED.match(image):
            error(app_dir + ": service '" + name + "' image must be pinned as repo:tag@sha256:digest")
        if ":latest" in image:
            error(app_dir + ": service '" + name + "' must not use the latest tag")

    # Templates are rendered with envsubst: a stray dollar sign in a script
    # would be replaced by an empty string.
    for template in glob.glob(os.path.join(app_dir, "*.template")):
        with open(template) as handle:
            if "$" in handle.read():
                error(template + ": contains '$', which envsubst would substitute")

if errors:
    print(str(len(errors)) + " problem(s) found")
    sys.exit(1)
print("OK: " + ", ".join(app_dirs))
