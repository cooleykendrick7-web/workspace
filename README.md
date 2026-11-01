# Workspace — Ken's money-opportunity board

Like ClaimBoard, but for paid work Ken can pick up:

- 🧪 **Product Testing** — sites that pay cash (or free products) to test products/apps
- 🤝 **Sponsorships** — platforms where brands pay Ken to sponsor / film their products (incl. UGC, no followers needed on beginner tiers)
- 🎬 **Casting (side job)** — paid acting / background / extra roles

Rules baked in (Ken's orders, 2026-11-01):
- **Admin board has NO password** — tap Admin and you're in (`/admin`).
- Main board buttons (Save / Applied / Booked / Pass) are open too, same as the admin.
- Pay ranges are what platforms publish / widely report — labeled as ranges, never guarantees.
- "Paid" counts only money actually received, entered in Admin.
- Legit casting never charges to audition — scam warning is on the board.

Run locally: `uvicorn app:app --port 8000`
Deploy: GitHub repo → Render Blueprint (render.yaml, Starter + 1GB disk at /data).
Seed data researched Nov 1, 2026 from platform pages + comparison sources (see app.py notes per entry).
