#!/usr/bin/env python3
"""Publish the Reel reserved by reserve.py.

Step 3 of the dupe-proof flow:  reserve.py -> commit & push state.json -> publish.py

By the time this runs, reserve.py has already built + processed the media
container and, crucially, state.json has already been advanced AND pushed. So
media_publish — the one non-idempotent call — runs last. If Instagram accepts
the Reel but this process dies before returning, the queue cursor is already
past this slot, so the next scheduled run will NOT re-post it.

reserved.json (written by reserve.py, not committed to git) carries the
container id to publish. If it is missing or has index=None (empty queue),
this is a no-op.

Env vars: IG_USER_ID, IG_ACCESS_TOKEN, GRAPH_HOST, GRAPH_VERSION.
(VIDEO_BASE_URL is only needed by reserve.py.)
"""
import json, os
import urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.environ.get("GRAPH_VERSION", "v21.0")
HOST = os.environ.get("GRAPH_HOST", "graph.instagram.com")
IG_USER = os.environ["IG_USER_ID"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
API = f"https://{HOST}/{GRAPH}"

RESERVED = os.path.join(HERE, "reserved.json")


def _req(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise SystemExit(f"Graph API error {e.code}: {detail}")


def publish(cid):
    return _req(f"{API}/{IG_USER}/media_publish",
                {"creation_id": cid, "access_token": TOKEN})


def main():
    if not os.path.exists(RESERVED):
        print("no reserved.json — reserve.py did not run or reserved nothing. skipping.")
        return

    reserved = json.load(open(RESERVED))
    cid = reserved.get("cid")
    i = reserved.get("index")
    if i is None or not cid:
        print("no slot reserved (queue empty). nothing to publish.")
        return

    print(f"publishing reserved index {i} ({reserved.get('file')}) via container {cid}")
    res = publish(cid)
    print(f"  published: {res}")


if __name__ == "__main__":
    main()
