# Outbed — free auto-poster (Instagram Reels, 3/day)

Publishes your meme Reels to Instagram automatically, **$0**:
- **GitHub Actions** cron runs 3×/day (free & unmetered on public repos).
- **Instagram Graph API** publishes each Reel (no fee).
- Videos are hosted **from this repo** via a free CDN — no S3/hosting bill.

One Reel per run × 3 runs/day. `posts.json` is the queue (101 posts, themes
interleaved); `state.json` tracks how many have gone out.

---

## What it costs
| Piece | Cost |
|---|---|
| Instagram Graph API publishing | $0 (no per-request fee) |
| GitHub Actions (public repo) | $0, unmetered |
| Video hosting (jsDelivr CDN of this repo) | $0 |
| Meta developer app / Business account | $0 |

Requirements the API imposes (already satisfied by the render pipeline):
Reels must be **9:16, 5–90 s, H.264** — our clips are 9:16 / 6–8 s / H.264. ✔

---

## One-time setup (~30 min)

### 1. Instagram account
Switch your IG to a **Professional (Business or Creator)** account
(IG app → Settings → *Account type and tools* → *Switch to professional*).
Link it to a **Facebook Page** (create a free Page if you don't have one):
IG app → Settings → *Accounts Center* / *Linked accounts*.

### 2. Meta developer app  (stays in *Development* mode — no App Review needed to post to **your own** account)
1. https://developers.facebook.com → *My Apps* → **Create App** → type **Business**.
2. Add product **Instagram Graph API** (a.k.a. Instagram).
3. In *App roles*, make sure your own user is Admin.

### 3. Get IG_USER_ID and IG_ACCESS_TOKEN
Use the **Graph API Explorer** (developers.facebook.com/tools/explorer):
1. Pick your app, click **Generate Access Token**, grant these permissions:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `business_management`.
2. Find your IG user id:
   - `GET /me/accounts` → note your Page's `id`.
   - `GET /{page-id}?fields=instagram_business_account` → that
     `instagram_business_account.id` is your **IG_USER_ID**.
3. Make the token long-lived (60 days):
   `GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-token}`
   → the returned token is **IG_ACCESS_TOKEN**.
   - *Better (never expires):* create a **System User** in
     business.facebook.com → *Business settings → Users → System users*,
     assign the app + Page, and generate a token with the same permissions.

### 4. Push this folder to a **public** GitHub repo
```
git init && git add . && git commit -m "outbed auto-poster"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 5. Add repo secrets + variable
Repo → *Settings → Secrets and variables → Actions*:
- **Secrets**: `IG_USER_ID`, `IG_ACCESS_TOKEN`
- **Variable**: `VIDEO_BASE_URL` =
  `https://cdn.jsdelivr.net/gh/<you>/<repo>@main/videos/`
  (jsDelivr serves the repo's videos over a CDN with the correct
  `video/mp4` type. Raw githubusercontent also works but MIME is less reliable.)

### 6. Turn it on
- Repo → *Actions* tab → enable workflows.
- Click **Post Outbed Reel → Run workflow** once to test (posts the next queued Reel now).
- After that the three daily crons run automatically.

---

## Schedule
Edit the `cron:` lines in `.github/workflows/post.yml`. They're **UTC**.
Defaults = 08:00 / 13:00 / 19:00 **IST**. For your timezone, subtract your
UTC offset from the local hour you want.

## Notes
- **Token expiry:** a long-lived user token lasts 60 days — refresh it before
  then, or use a System User token (no expiry). If posting suddenly stops,
  the token likely expired.
- **Queue done:** after all 101 publish, runs just log "queue empty". Add more
  by appending to `posts.json` and dropping the mp4s in `videos/`.
- **Re-run a post:** edit `state.json` `next` back to the index you want.
- **jsDelivr cache:** new files can take a few minutes to appear on the CDN.
