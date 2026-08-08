#!/usr/bin/env python3
"""Publish the next queued meme Reel to Instagram via the Graph API.

Runs once per invocation (GitHub Actions calls it 3x/day). Flow:
  1. read posts.json + state.json -> pick posts[state.next]
  2. create a REELS media container (public video_url + caption)
  3. poll container status until FINISHED
  4. publish the container
  5. advance state.next and write state.json (workflow commits it)

Env vars (GitHub Actions secrets / vars):
  IG_USER_ID        Instagram user id (numeric). For the Instagram-login flow
                    this is the id from GET graph.instagram.com/me?fields=user_id
  IG_ACCESS_TOKEN   long-lived token with content-publish perms
  VIDEO_BASE_URL    public base URL for the videos/ dir, WITH trailing slash
                    e.g. https://cdn.jsdelivr.net/gh/<user>/<repo>@main/videos/
  GRAPH_HOST        API host. Use "graph.instagram.com" for the Instagram-login
                    flow (API setup with Instagram login) or "graph.facebook.com"
                    for the Facebook-login flow. Default graph.instagram.com.
  GRAPH_VERSION     optional, default v21.0
"""
import json, os, sys, time
import urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.environ.get("GRAPH_VERSION", "v21.0")
HOST = os.environ.get("GRAPH_HOST", "graph.instagram.com")
IG_USER = os.environ["IG_USER_ID"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
BASE = os.environ["VIDEO_BASE_URL"]
API = f"https://{HOST}/{GRAPH}"


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


def wait_finished(cid, tries=30, delay=10):
    for _ in range(tries):
        r = _req(f"{API}/{cid}?fields=status_code&access_token={urllib.parse.quote(TOKEN)}")
        s = r.get("status_code")
        if s == "FINISHED":
            return
        if s == "ERROR":
            raise SystemExit(f"container processing failed: {r}")
        time.sleep(delay)
    raise SystemExit("timed out waiting for container to finish processing")


def publish(cid):
    return _req(f"{API}/{IG_USER}/media_publish",
                {"creation_id": cid, "access_token": TOKEN})


def main():
    posts = json.load(open(os.path.join(HERE, "posts.json")))
    state = json.load(open(os.path.join(HERE, "state.json")))
    i = state.get("next", 0)
    if i >= len(posts):
        print("queue empty — all posts published. nothing to do.")
        return
    item = posts[i]
    video_url = BASE + urllib.parse.quote(item["file"])
    print(f"[{i+1}/{len(posts)}] publishing {item['file']}")
    cid = create_container(video_url, item["caption"])
    print(f"  container {cid} created; waiting for processing…")
    wait_finished(cid)
    res = publish(cid)
    print(f"  published: {res}")
    state["next"] = i + 1
    with open(os.path.join(HERE, "state.json"), "w") as f:
        json.dump(state, f, indent=2)
    print(f"  state advanced -> next={state['next']}")


if __name__ == "__main__":
    main()
