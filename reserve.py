#!/usr/bin/env python3
"""Reserve the next queued Reel: build + process its media container, then
advance the queue cursor — WITHOUT publishing yet.

This is step 1 of a two-step, dupe-proof publish flow:

  reserve.py  ->  commit & push state.json  ->  publish.py

Why split it up:
  The old single-script flow published first and advanced state.json last, so
  any failure between a successful Instagram publish and the state push caused
  the *same* Reel to be re-posted on the next scheduled run (the "posted at
  night, posted again next morning" bug).

  Splitting the work fixes every failure mode:
    * container create / processing fails here -> state is NOT advanced and no
      reserved.json is written -> the next run simply retries this same Reel.
    * the push of state.json fails (step 2) -> publish.py never runs (the job
      stops on a failed step) -> the next run retries this same Reel.
    * publish (step 3) fails *after* Instagram already accepted the Reel ->
      state.json was already advanced+pushed -> the next run moves on instead
      of re-posting. Worst case is one skipped Reel, never a duplicate.

Only container creation + processing happen here (both are safe to retry
because nothing is posted yet). The single non-idempotent call — media_publish
— lives in publish.py and runs only after state.json is committed.

Env vars: same as publish.py (IG_USER_ID, IG_ACCESS_TOKEN, VIDEO_BASE_URL,
GRAPH_HOST, GRAPH_VERSION).
"""
import json, os, time
import urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.environ.get("GRAPH_VERSION", "v21.0")
HOST = os.environ.get("GRAPH_HOST", "graph.instagram.com")
IG_USER = os.environ["IG_USER_ID"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
BASE = os.environ["VIDEO_BASE_URL"]
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


def create_container(video_url, caption):
    r = _req(f"{API}/{IG_USER}/media", {
        "media_type": "REELS", "video_url": video_url,
        "caption": caption, "access_token": TOKEN,
    })
    return r["id"]


def wait_finished(cid, tries=90, delay=10):
    # Reels processing is usually <1 min, but Instagram occasionally stalls a
    # container for several minutes. Poll patiently (up to ~15 min). On timeout
    # we exit non-zero WITHOUT advancing state, so the next scheduled slot
    # simply retries this same post (nothing has been published yet).
    for _ in range(tries):
        r = _req(f"{API}/{cid}?fields=status_code&access_token={urllib.parse.quote(TOKEN)}")
        s = r.get("status_code")
        if s == "FINISHED":
            return
        if s == "ERROR":
            raise SystemExit(f"container processing failed: {r}")
        time.sleep(delay)
    raise SystemExit("timed out waiting for container to finish processing (will retry next run)")


def main():
    posts = json.load(open(os.path.join(HERE, "posts.json")))
    state = json.load(open(os.path.join(HERE, "state.json")))
    i = state.get("next", 0)

    if i >= len(posts):
        print("queue empty — all posts published. nothing to reserve.")
        # Clear any stale reservation so publish.py is a no-op this run.
        with open(RESERVED, "w") as f:
            json.dump({"index": None}, f)
        return

    item = posts[i]
    video_url = BASE + urllib.parse.quote(item["file"])
    print(f"[{i+1}/{len(posts)}] reserving {item['file']}")

    cid = create_container(video_url, item["caption"])
    print(f"  container {cid} created; waiting for processing…")
    wait_finished(cid)
    print("  container FINISHED — safe to reserve slot")

    # Record what publish.py must publish, then advance the cursor. The workflow
    # commits+pushes state.json BEFORE running publish.py, so once we get here
    # the slot is permanently consumed and can never be re-posted.
    with open(RESERVED, "w") as f:
        json.dump({"index": i, "file": item["file"], "cid": cid}, f, indent=2)

    state["next"] = i + 1
    with open(os.path.join(HERE, "state.json"), "w") as f:
        json.dump(state, f, indent=2)
    print(f"  reserved cid {cid}; state advanced -> next={state['next']}")


if __name__ == "__main__":
    main()
