import json, os, time, urllib.parse, urllib.request, urllib.error
GRAPH=os.environ.get("GRAPH_VERSION","v21.0"); HOST=os.environ.get("GRAPH_HOST","graph.instagram.com")
IG=os.environ["IG_USER_ID"]; TOKEN=os.environ["IG_ACCESS_TOKEN"]
URL=os.environ["VIDEO_URL"]; CAP=os.environ.get("CAPTION","")
API=f"https://{HOST}/{GRAPH}"
def req(u,data=None):
    body=urllib.parse.urlencode(data).encode() if data else None
    r=urllib.request.Request(u,data=body,method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(r,timeout=60) as x: return json.load(x)
    except urllib.error.HTTPError as e: raise SystemExit(f"{e.code}: {e.read().decode()}")
print("publishing",URL)
cid=req(f"{API}/{IG}/media",{"media_type":"REELS","video_url":URL,"caption":CAP,"access_token":TOKEN})["id"]
print("container",cid)
for _ in range(90):
    s=req(f"{API}/{cid}?fields=status_code&access_token={urllib.parse.quote(TOKEN)}").get("status_code")
    if s=="FINISHED": break
    if s=="ERROR": raise SystemExit("processing error")
    time.sleep(10)
else: raise SystemExit("timeout")
print("published",req(f"{API}/{IG}/media_publish",{"creation_id":cid,"access_token":TOKEN}))
