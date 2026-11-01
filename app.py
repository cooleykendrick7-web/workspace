"""
Workspace — Ken's money-opportunity board.
Like ClaimBoard, but for:
  1) Paid product testing (test)
  2) Paid sponsorships / brand deals (sponsor)
  3) Paid casting roles — the side job (casting)

Admin board has NO password by Ken's order (2026-11-01): click Admin and you're in.
Data is real SQLite, computed live on every request. No fake numbers.
Pay ranges are what each platform publishes / is widely reported to pay —
they are NOT guarantees. Every entry links to the real platform.
"""
import os, datetime, sqlite3
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).parent
DB_PATH = os.environ.get("WORKSPACE_DB", str(BASE / "workspace.db"))

app = FastAPI(title="Workspace", version="1.3.0")
SIGNUP_STATES = ("not_started", "queued", "started", "done", "needs_ken")
BATCH1 = ("billo", "collabstr", "mycastingfile", "usertesting", "respondent")  # easiest free signups, first auto-signup run

CATEGORIES = ("test", "sponsor", "casting")
STATUSES = ("found", "saved", "applied", "booked", "paid", "passed")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# slug, title, category, platform, pay_label, pay_low, pay_high, url, location, requirements, note
SEED = [
    # ---------- PAID PRODUCT TESTING ----------
    ("usertesting", "Test websites & apps talking out loud", "test", "UserTesting", "$10–$60 per test · $30–$120 live", 10, 120, "https://www.usertesting.com/get-paid-to-test", "Remote / from home", "18+, PayPal, mic + screen record, pass a practice test", "Biggest legit tester platform. 10–20 min tests pay ~$10, live interviews pay a lot more. PayPal ~14 days after."),
    ("respondent", "Paid research studies & product tests", "test", "Respondent", "$50–$250 per study · avg ~$75–$95", 50, 250, "https://www.respondent.io", "Remote + in-person", "Profile + screeners, LinkedIn helps for pro studies", "Highest pay per study on this list. In-home product tests, interviews, diary studies. Paid via Tremendous."),
    ("user-interviews", "Product tests, interviews & focus groups", "test", "User Interviews", "$20–$150+ per study · avg ~$45", 20, 150, "https://www.userinterviews.com/hello", "Remote / nationwide", "Free profile, answer screeners fast", "Most study volume. $50–$150/hr is common for interviews. Paid a few days after via Tremendous / gift card."),
    ("dscout", "Phone diary missions testing products/apps", "test", "dscout", "$25–$150 per mission", 25, 150, "https://dscout.com/participate-in-research-studies", "Remote — phone app", "Smartphone, short video answers for screeners", "Missions = record short videos/photos using a product over days. ~$1/min average. PayPal after approval."),
    ("utest", "Paid app & website bug / usability testing", "test", "uTest", "Varies per project — paid per approved bug/test", 10, 100, "https://www.utest.com", "Remote", "Follow detailed test instructions, any device helps", "Real paid testing work, not surveys. Projects board updates daily. Paid twice a month."),
    ("pinecone", "Test new products at home + surveys", "test", "Pinecone Research", "$3–$5 per survey/test + keep the product", 3, 10, "https://www.pineconeresearch.com", "US, at home", "Invite/panel signup, US address for shipping", "Nielsen panel. Small cash, but you keep products that haven't launched yet. PayPal in ~48 hrs."),
    ("trymata", "Website & app usability tests", "test", "Trymata (TryMyUI)", "$5–$30 per test", 5, 30, "https://trymata.com", "Remote", "Mic + screen record, 15–20 min per test", "Like UserTesting, smaller. ~$10 standard test, PayPal after approval."),
    ("userlytics", "Site, app, ad & prototype tests", "test", "Userlytics", "$5–$90 per test", 5, 90, "https://www.userlytics.com/tester", "Remote", "Webcam + mic, 20–40 min tests", "Paid every ~2 weeks to PayPal, about 15 days after a test."),
    ("playbookux", "Website & app video tests", "test", "PlaybookUX", "$10–$100 per test", 10, 100, "https://www.playbookux.com", "Remote", "Screen + voice recording", "Tests pay by length/complexity. PayPal within ~8 days."),
    ("curion", "Taste / try food, beauty & home products in studies", "test", "Curion", "$40–$250 per 30–60 min study", 40, 250, "https://www.curion.com", "In-person near Curion centers + some home tests", "Free panel profile, wait for invite match", "Real consumer product studies — food, drinks, personal care. Highest in-person range on the testing side."),
    ("influenster", "Free product boxes (VoxBox) for honest reviews", "test", "Influenster", "Free products — no cash", 0, 0, "https://www.influenster.com", "At home, US shipping", "Profile + reviews, disclose free product (FTC rule)", "No cash — you keep full-size beauty/home products. Good starter, builds review history brands look at."),
    ("hometesterclub", "Free household & grocery products to test at home", "test", "Home Tester Club", "Free products — no cash guarantee", 0, 0, "https://www.hometesterclub.com", "At home", "Apply per product, write honest review", "Free full-size products. Pairs well with the cash platforms above."),
    ("bzzagent", "Free sample campaigns for honest word-of-mouth", "test", "BzzAgent", "Free products — no cash", 0, 0, "https://www.bzzagent.com", "At home", "Profile matched to campaigns", "Free consumer products in limited campaigns. Honest review expected, disclosure required."),

    # ---------- PAID SPONSORSHIPS / BRAND DEALS ----------
    ("collabstr", "Brands buy sponsored posts/UGC from your profile", "sponsor", "Collabstr", "$50–$5,000+ per collab — you set your price", 50, 5000, "https://collabstr.com", "Remote — IG / TikTok / YouTube / Twitch", "No follower minimum, profile reviewed", "Best starter marketplace: money held in escrow up front, Collabstr keeps 15%. You pick what to accept."),
    ("billo", "Paid UGC product videos for brands (no posting needed)", "sponsor", "Billo", "$50–$250 per video", 50, 250, "https://billo.app", "Remote — film at home", "No followers or experience needed", "Beginner-friendly. Brand sends product + brief, you film a short video, brand runs it as an ad. Fast first paid gigs."),
    ("joinbrands", "UGC videos & sponsored posts marketplace", "sponsor", "JoinBrands", "$25–$60+ per video, scales with level", 25, 200, "https://joinbrands.com", "Remote — TikTok / IG / Amazon", "Free to join, build level with completed jobs", "Fast approvals for new creators, first paid project often inside the first week."),
    ("cohley", "Vetted creator campaigns for big brands", "sponsor", "Cohley", "$200 minimum per campaign recommended", 200, 750, "https://www.cohley.com", "Remote", "Human review to join, portfolio up to 9 pieces, 18+", "Quality over quantity — fewer creators, bigger budgets (Bose, Foot Locker, TOMS level brands)."),
    ("aspire", "Brand programs & ambassador deals", "sponsor", "Aspire", "$200+ per deal — brand-negotiated", 200, 5000, "https://creators.aspireiq.com", "Remote — all major platforms", "1,000+ followers for marketplace", "800+ brands (Walmart, HelloFresh, Dyson, Samsung). $100M+ paid to creators total. Step-up platform once you have samples."),
    ("insense", "Paid social UGC + whitelisted ads", "sponsor", "Insense", "$100–$500+ per project", 100, 500, "https://insense.pro", "Remote — TikTok / IG", "Portfolio helps, 5+ projects gets best briefs", "Built for paid social ads. Strong mid-range pay per video."),
    ("hashtagpaid", "Matched brand campaigns (#paid)", "sponsor", "#paid", "$250–$5,000 per campaign", 250, 5000, "https://hashtagpaid.com", "US / Canada — IG / TikTok / YouTube", "Typically 5,000–10,000+ followers, public account", "Bigger campaigns with usage rights paid on top. 14–30 day payout after approval."),
    ("amazon-influencer", "Amazon storefront + product video commissions", "sponsor", "Amazon Influencer Program", "Commission-based — varies by sales", 0, 1000, "https://www.amazon.com/influencers", "Remote — your Amazon storefront", "Application-based, needs social account", "Your own storefront + shoppable videos. Creator Connections adds paid brand campaigns on top of commissions."),
    ("tiktok-one", "TikTok brand projects & TikTok Shop", "sponsor", "TikTok One / Creator Marketplace", "Brand-set — varies per project", 50, 5000, "https://www.tiktok.com/creators/creator-marketplace", "TikTok app", "1,000 followers for brand projects, 18+", "TikTok's own brand-deal door. TikTok says One Pay takes no cut on brand projects."),
    ("passionfroot", "Your sponsorship booking page + brand network", "sponsor", "Passionfroot", "You set packages — 0% on your own deals, 15% on network deals", 100, 5000, "https://www.passionfroot.me", "Remote — YouTube / newsletter / podcast / social", "Free, B2B vetting for marketplace listing", "One page where sponsors book you, with invoicing handled. Good home base to send every brand to."),
    ("socialcat", "Micro-creator brand deals", "sponsor", "Social Cat", "Varies — gifted + paid collabs", 25, 500, "https://thesocialcat.com", "Remote — IG / TikTok", "1,000+ followers", "Built for micro-influencers. 14–21 day payouts via PayPal on paid deals."),

    # ---------- PAID CASTING — SIDE JOB ----------
    ("backstage", "Film, TV, commercial & background casting calls", "casting", "Backstage", "Up to $375/day listed · background $100–$300/day", 100, 1246, "https://www.backstage.com/casting", "Nationwide + remote self-tapes", "Browse free, subscription to apply (~$20/mo), no agent needed", "Biggest front door for beginners: 15,000+ jobs. Filter PAID only. SAG day rate is $1,246/day, background $224–$231/day."),
    ("central-casting", "Background / extra work — the industry standard", "casting", "Central Casting", "$100–$200/day non-union · $231/day SAG background", 100, 231, "https://www.centralcasting.com", "LA / NYC / Atlanta / New Orleans hubs + more", "FREE registration, everyday phone photos are fine", "Gold standard for extras. No experience needed. Never pay an upfront fee — legit casting doesn't charge to audition."),
    ("actors-access", "Film & TV breakdowns (where the big projects post)", "casting", "Actors Access", "Project pay varies — SAG scale and up", 200, 1246, "https://actorsaccess.com", "Nationwide, self-tape from anywhere", "Free profile, ~$2 per submission or $68/yr unlimited", "Industry standard for episodic TV & features. The one pros say to get first for film/TV."),
    ("casting-networks", "Commercials & branded content casting", "casting", "Casting Networks", "Commercial pay varies — often $500+/day + usage", 200, 2000, "https://www.castingnetworks.com", "Nationwide, big in LA/NYC", "~$29.99/mo subscription", "The dominant platform for commercials — where most ad casting offices live."),
    ("project-casting", "Free casting call board — film, TV, commercials, extras", "casting", "Project Casting", "Varies per call — many paid background gigs", 100, 1000, "https://projectcasting.com", "Nationwide, strong in Southeast & LA", "Free to browse, free tier to apply", "Good free starter alongside Backstage. Verify each listing — quality varies on aggregators."),
    ("mycastingfile", "Paid movie & TV extra roles near you", "casting", "MyCastingFile", "Pay shown per call — production pays you direct", 100, 300, "https://mycastingfile.com", "By location — open calls near you", "FREE to join & apply, 2 photos, no experience needed", "116,000+ days on set booked through it since 2020. Free profile is enough to get booked."),
    ("vertical-casting", "Vertical drama series roles (ReelShort / DramaBox style)", "casting", "Vertical Casting Calls", "Leads $1,000–$1,500/day · supporting $250–$500 · extras $150–$200/day", 150, 1500, "https://www.verticalcastingcalls.com", "Shoots nationwide, self-tape from anywhere", "Free alerts, no membership fee", "The hidden fast lane: 400+ vertical series a year, 7–10 day shoots, thousands of paid roles most actors never see."),
]

def init_db():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS opportunities(
      slug TEXT PRIMARY KEY, title TEXT, category TEXT, platform TEXT,
      pay_label TEXT, pay_low REAL, pay_high REAL, url TEXT,
      location TEXT, requirements TEXT, note TEXT,
      status TEXT DEFAULT 'found', paid_amount REAL DEFAULT 0,
      updated_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS punches(
      id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, ts TEXT)""")
    cols = {r[1] for r in c.execute("PRAGMA table_info(opportunities)")}
    if "signup_state" not in cols:
        c.execute("ALTER TABLE opportunities ADD COLUMN signup_state TEXT DEFAULT 'not_started'")
    if "apply_approved" not in cols:
        c.execute("ALTER TABLE opportunities ADD COLUMN apply_approved INTEGER DEFAULT 0")
    if "apply_note" not in cols:
        c.execute("ALTER TABLE opportunities ADD COLUMN apply_note TEXT DEFAULT ''")
    for row in SEED:
        c.execute("INSERT OR IGNORE INTO opportunities(slug,title,category,platform,pay_label,pay_low,pay_high,url,location,requirements,note,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,'found',?)",
                  (*row, datetime.datetime.utcnow().isoformat()))
    for slug in BATCH1:
        c.execute("UPDATE opportunities SET signup_state='queued' WHERE slug=? AND (signup_state IS NULL OR signup_state='not_started')", (slug,))
    c.commit(); c.close()
init_db()

@app.middleware("http")
async def headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp

@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "workspace", "version": "1.3.0"}

@app.get("/api/opportunities")
async def api_list(category: str | None = None):
    c = db()
    if category and category in CATEGORIES:
        rows = c.execute("SELECT * FROM opportunities WHERE category=? ORDER BY pay_high DESC", (category,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM opportunities ORDER BY category, pay_high DESC").fetchall()
    c.close()
    return [dict(r) for r in rows]

@app.get("/api/summary")
async def api_summary():
    c = db(); rows = c.execute("SELECT * FROM opportunities").fetchall(); c.close()
    paid = sum((r["paid_amount"] or 0) for r in rows if r["status"] == "paid")
    by_cat = {cat: sum(1 for r in rows if r["category"] == cat) for cat in CATEGORIES}
    by_status = {s: sum(1 for r in rows if r["status"] == s) for s in STATUSES}
    active = [r for r in rows if r["status"] in ("saved", "applied", "booked")]
    return {
        "paid_total": round(paid, 2),
        "total": len(rows),
        "by_category": by_cat,
        "counts": by_status,
        "active_count": len(active),
        "active_potential_low": round(sum((r["pay_low"] or 0) for r in active), 2),
        "active_potential_high": round(sum((r["pay_high"] or 0) for r in active), 2),
        "all_potential_high": round(sum((r["pay_high"] or 0) for r in rows if r["status"] != "passed"), 2),
        "updated": datetime.datetime.utcnow().isoformat(),
    }

class StatusIn(BaseModel):
    status: str

@app.patch("/api/opportunities/{slug}")
async def api_set_status(slug: str, body: StatusIn):
    # No password by Ken's order — admin is open.
    if body.status not in STATUSES:
        raise HTTPException(400, "Invalid status.")
    c = db()
    cur = c.execute("UPDATE opportunities SET status=?, updated_at=? WHERE slug=?",
                    (body.status, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug, "status": body.status}

class OppIn(BaseModel):
    slug: str; title: str; category: str = "test"; platform: str = ""
    pay_label: str = ""; pay_low: float | None = None; pay_high: float | None = None
    url: str = ""; location: str = ""; requirements: str = ""; note: str = ""
    status: str = "found"

@app.post("/api/admin/opportunities")
async def api_upsert(body: OppIn):
    if body.category not in CATEGORIES:
        raise HTTPException(400, "Invalid category.")
    if body.status not in STATUSES:
        raise HTTPException(400, "Invalid status.")
    c = db()
    c.execute("""INSERT INTO opportunities(slug,title,category,platform,pay_label,pay_low,pay_high,url,location,requirements,note,status,updated_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(slug) DO UPDATE SET title=excluded.title, category=excluded.category, platform=excluded.platform,
      pay_label=excluded.pay_label, pay_low=excluded.pay_low, pay_high=excluded.pay_high, url=excluded.url,
      location=excluded.location, requirements=excluded.requirements, note=excluded.note, updated_at=excluded.updated_at""",
      (body.slug, body.title, body.category, body.platform, body.pay_label, body.pay_low, body.pay_high,
       body.url, body.location, body.requirements, body.note, body.status, datetime.datetime.utcnow().isoformat()))
    c.commit(); c.close()
    return {"ok": True, "slug": body.slug}

class PaidIn(BaseModel):
    amount: float

@app.post("/api/admin/opportunities/{slug}/paid")
async def api_paid(slug: str, body: PaidIn):
    c = db()
    cur = c.execute("UPDATE opportunities SET status='paid', paid_amount=?, updated_at=? WHERE slug=?",
                    (body.amount, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True}

@app.delete("/api/admin/opportunities/{slug}")
async def api_delete(slug: str):
    c = db()
    cur = c.execute("DELETE FROM opportunities WHERE slug=?", (slug,))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True}

def _clock_state(c):
    rows = c.execute("SELECT * FROM punches ORDER BY id ASC").fetchall()
    clocked_in = False; since = None; total = 0.0; last_in = None
    for r in rows:
        t = datetime.datetime.fromisoformat(r["ts"])
        if r["action"] == "in":
            clocked_in = True; since = r["ts"]; last_in = t
        elif r["action"] == "out" and clocked_in and last_in is not None:
            total += (t - last_in).total_seconds(); clocked_in = False; since = None; last_in = None
    hist = c.execute("SELECT * FROM punches ORDER BY id DESC LIMIT 12").fetchall()
    return {"clocked_in": clocked_in, "since": since,
            "total_seconds_done": int(total),
            "history": [dict(r) for r in hist]}

@app.get("/api/operator/clock")
async def api_clock_get():
    c = db(); st = _clock_state(c); c.close()
    return st

class ClockIn(BaseModel):
    action: str

@app.post("/api/operator/clock")
async def api_clock_post(body: ClockIn):
    # Ken's time card — no password by his order. Sliding the card IS the punch.
    if body.action not in ("in", "out"):
        raise HTTPException(400, "Action must be 'in' or 'out'.")
    c = db(); st = _clock_state(c)
    if body.action == "in" and st["clocked_in"]:
        c.close(); raise HTTPException(400, "Already clocked in.")
    if body.action == "out" and not st["clocked_in"]:
        c.close(); raise HTTPException(400, "Not clocked in.")
    ts = datetime.datetime.utcnow().isoformat()
    c.execute("INSERT INTO punches(action, ts) VALUES(?, ?)", (body.action, ts))
    c.commit(); st = _clock_state(c); c.close()
    return {"ok": True, "action": body.action, "ts": ts, **st}

@app.get("/api/operator/summary")
async def api_operator_summary():
    c = db(); rows = c.execute("SELECT * FROM opportunities").fetchall(); c.close()
    paid = sum((r["paid_amount"] or 0) for r in rows if r["status"] == "paid")
    def cnt(key, val): return sum(1 for r in rows if r[key] == val)
    needs_ken = [dict(r) for r in rows if (r["signup_state"] or "") == "needs_ken"]
    queued = [dict(r) for r in rows if (r["signup_state"] or "") == "queued"]
    signed_up = [dict(r) for r in rows if (r["signup_state"] or "") == "done"]
    approved = [dict(r) for r in rows if (r["apply_approved"] or 0) == 1]
    return {
        "service": "workspace", "version": "1.3.0",
        "total": len(rows),
        "by_category": {cat: cnt("category", cat) for cat in CATEGORIES},
        "by_status": {s: cnt("status", s) for s in STATUSES},
        "by_signup": {s: cnt("signup_state", s) for s in SIGNUP_STATES},
        "paid_total": round(paid, 2),
        "signed_up": [{"slug": r["slug"], "platform": r["platform"]} for r in signed_up],
        "queued_for_signup": [{"slug": r["slug"], "platform": r["platform"], "category": r["category"]} for r in queued],
        "needs_ken": [{"slug": r["slug"], "platform": r["platform"], "note": r["note"]} for r in needs_ken],
        "approved_to_apply": [{"slug": r["slug"], "platform": r["platform"], "category": r["category"],
                               "status": r["status"], "signup_state": r["signup_state"] or "not_started",
                               "apply_note": r["apply_note"] or ""} for r in approved],
        "approved_count": len(approved),
        "next_actions": [
            "APPLY QUEUE: when Ken taps Approve on a gig, Milli does the applying herself — pitches, submissions, screeners she can answer from his confirmed profile facts. Unknown screener answers and anything needing a signature, contract, payment, or Ken's voice/recording stop and get noted on the item.",
            "Batch 1 accounts: Collabstr / MyCastingFile / Respondent / UserTesting created; Billo is iPhone-app-only (Ken). Finishing steps still Ken's: UserTesting income + work status, MyCastingFile emergency contact, email verification taps, Collabstr Go Live identity check.",
            "Ken-only steps that stop any run cold: email verification codes, PayPal linking, any ID/tax/address-for-payment form.",
        ],
        "updated": datetime.datetime.utcnow().isoformat(),
    }

class SignupIn(BaseModel):
    signup_state: str

@app.patch("/api/opportunities/{slug}/signup")
async def api_set_signup(slug: str, body: SignupIn):
    # No password by Ken's order — operator panel is open.
    if body.signup_state not in SIGNUP_STATES:
        raise HTTPException(400, "Invalid signup_state.")
    c = db()
    cur = c.execute("UPDATE opportunities SET signup_state=?, updated_at=? WHERE slug=?",
                    (body.signup_state, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug, "signup_state": body.signup_state}

class ApproveIn(BaseModel):
    approved: bool

@app.patch("/api/opportunities/{slug}/approve")
async def api_set_approve(slug: str, body: ApproveIn):
    # Ken taps Approve on the board -> Milli does the actual applying (Ken's order 2026-11-01).
    # No password by Ken's order — the board is open.
    c = db()
    cur = c.execute("UPDATE opportunities SET apply_approved=?, updated_at=? WHERE slug=?",
                    (1 if body.approved else 0, datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug, "apply_approved": body.approved}

class ApplyNoteIn(BaseModel):
    note: str

@app.patch("/api/opportunities/{slug}/apply-note")
async def api_set_apply_note(slug: str, body: ApplyNoteIn):
    # Milli records what happened when she applied (or what's blocking it).
    c = db()
    cur = c.execute("UPDATE opportunities SET apply_note=?, updated_at=? WHERE slug=?",
                    (body.note[:500], datetime.datetime.utcnow().isoformat(), slug))
    c.commit(); n = cur.rowcount; c.close()
    if not n: raise HTTPException(404, "Not found.")
    return {"ok": True, "slug": slug}

app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(str(BASE / "static" / "index.html"))

@app.get("/operator", response_class=HTMLResponse)
async def operator():
    return FileResponse(str(BASE / "static" / "operator.html"))

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    return FileResponse(str(BASE / "static" / "admin.html"))

@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(str(BASE / "static" / "manifest.webmanifest"), media_type="application/manifest+json")

@app.get("/sw.js")
async def sw():
    return FileResponse(str(BASE / "static" / "sw.js"), media_type="application/javascript")
