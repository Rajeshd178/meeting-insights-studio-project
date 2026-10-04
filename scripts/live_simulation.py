"""
Meeting Studio — Live Meeting Simulation Script
Simulates browser microphone chunk streaming to test the live pipeline end-to-end without physical hardware.
"""

import sys
import time
from pathlib import Path

# Ensure root is in path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app import app

def run_simulation():
    print("==================================================")
    print("Meeting Insights Studio: Live Simulation Runner")
    print("==================================================")

    client = app.test_client()

    # 1. Start live session
    print("\n[Step 1] Starting Live Session...")
    res = client.post("/api/live/start", json={
        "title": "Live Pipeline Verification Stream",
        "language": "en",
        "confidential": False
    })
    data = res.get_json()
    assert res.status_code == 200 and data.get("ok"), f"Failed to start live session: {data}"
    session_id = data["data"]["session_id"]
    print(f"✓ Live Session Initialized: {session_id}")

    # 2. Stream simulated 15-second audio chunks
    print("\n[Step 2] Streaming 4 Sequential 15-Second Audio Chunks...")
    for seq in range(4):
        fake_audio = b"MOCK_AUDIO_DATA_FOR_SIMULATION_PURPOSES" * 20
        res = client.post(
            f"/api/live/{session_id}/chunk",
            data={
                "seq": str(seq),
                "client_start": str(seq * 15.0),
                "audio": (open(__file__, "rb"), f"chunk_{seq}.webm")
            },
            content_type="multipart/form-data"
        )
        cdata = res.get_json()
        print(f"  → Ingested Chunk #{seq} @ {seq * 15}s: {cdata.get('data', {}).get('status')}")
        time.sleep(0.5)

    # 3. Poll updates
    print("\n[Step 3] Polling Live Updates...")
    res = client.get(f"/api/live/{session_id}/updates?since=-1")
    udata = res.get_json()
    updates = udata.get("data", {})
    print(f"  → Segments Count: {len(updates.get('segments', []))}")
    print(f"  → Running Summary Bullets: {len(updates.get('running_summary', {}).get('bullets', []))}")
    print(f"  → Tentative Action Items: {len(updates.get('tentative_items', []))}")

    # 4. Generate Catch-up Summary
    print("\n[Step 4] Requesting 5-Line Catch-Up Summary...")
    res = client.post(f"/api/live/{session_id}/catchup")
    cdata = res.get_json()
    bullets = cdata.get("data", {}).get("catchup_bullets", [])
    for b in bullets:
        print(f"  • {b}")

    # 5. Stop live session & handoff to pipeline
    print("\n[Step 5] Finalizing Live Session & Transitioning to Pipeline...")
    res = client.post(f"/api/live/{session_id}/stop")
    sdata = res.get_json()
    print(f"✓ Stop Response: {sdata}")

    print("\n==================================================")
    print("Live Meeting Simulation Completed Successfully!")
    print("==================================================")

if __name__ == "__main__":
    run_simulation()
