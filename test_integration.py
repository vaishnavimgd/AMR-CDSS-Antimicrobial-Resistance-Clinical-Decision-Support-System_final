"""
End-to-End Integration Test for the AMR Diagnostic System.

This script:
  1. Starts the FastAPI backend via uvicorn in a subprocess
  2. Waits for the server to become healthy
  3. Uploads backend/test.fasta to POST /upload-fasta
  4. Validates the JSON response structure and content
  5. Prints a pass/fail report
  6. Shuts down the backend
"""

import json
import os
import subprocess
import sys
import time

import requests

# ─── Configuration ───────────────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
TEST_FASTA = os.path.join(BACKEND_DIR, "test.fasta")
API_BASE = "http://127.0.0.1:8000"
STARTUP_TIMEOUT = 60  # seconds to wait for the server to start
REQUIRED_KEYS = ["file_id", "filename", "num_sequences", "genes_detected",
                 "predictions", "warnings", "anomaly", "message"]

# ─── Helpers ─────────────────────────────────────────────────────────────────

passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {label}")
    else:
        failed += 1
        msg = f"  ❌ {label}"
        if detail:
            msg += f" — {detail}"
        print(msg)


def wait_for_server(url: str, timeout: int) -> bool:
    """Poll the health endpoint until the server is ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    return False


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    global passed, failed
    print("=" * 60)
    print("AMR Integration Test")
    print("=" * 60)

    # 1. Pre-flight checks
    print("\n📋 Pre-flight checks")
    check("test.fasta exists", os.path.isfile(TEST_FASTA))
    check("gene_scanner.exe exists",
          os.path.isfile(os.path.join(BACKEND_DIR, "gene_scanner.exe")))

    # 2. Start backend
    print("\n🚀 Starting backend server…")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        healthy = wait_for_server(f"{API_BASE}/", STARTUP_TIMEOUT)
        check("Backend server started", healthy,
              "Server did not respond within timeout" if not healthy else "")

        if not healthy:
            print("\n⛔ Cannot continue — server not reachable.")
            return

        # 3. Health endpoint check
        print("\n🏥 Health check")
        r = requests.get(f"{API_BASE}/")
        check("GET / returns 200", r.status_code == 200)
        check("GET / returns {status: ok}", r.json().get("status") == "ok")

        # 4. Upload FASTA
        print("\n📤 Upload test.fasta")
        with open(TEST_FASTA, "rb") as fasta:
            r = requests.post(
                f"{API_BASE}/upload-fasta",
                files={"file": ("test.fasta", fasta, "text/plain")},
                timeout=120,
            )
        check("POST /upload-fasta returns 200", r.status_code == 200,
              f"got {r.status_code}: {r.text[:200]}" if r.status_code != 200 else "")

        if r.status_code != 200:
            print("\n⛔ Cannot validate response — upload failed.")
            return

        result = r.json()
        print(f"\n📦 Response JSON:\n{json.dumps(result, indent=2)}")

        # 5. Validate response structure
        print("\n🔍 Validating response structure")
        for key in REQUIRED_KEYS:
            check(f"Key '{key}' present", key in result)

        check("file_id is a string", isinstance(result.get("file_id"), str))
        check("filename is 'test.fasta'", result.get("filename") == "test.fasta")
        check("num_sequences is int", isinstance(result.get("num_sequences"), int))
        check("genes_detected is a list", isinstance(result.get("genes_detected"), list))
        check("predictions is a dict", isinstance(result.get("predictions"), dict))
        check("warnings is a list", isinstance(result.get("warnings"), list))
        check("anomaly is a bool", isinstance(result.get("anomaly"), bool))
        check("message is a string", isinstance(result.get("message"), str))

        # 6. Validate predictions content
        print("\n🧬 Validating predictions")
        preds = result.get("predictions", {})
        check("predictions is non-empty", len(preds) > 0,
              f"got {len(preds)} antibiotics")
        for abx, status in preds.items():
            check(f"  {abx} = {status}",
                  status in ("Resistant", "Susceptible", "Intermediate", "Unknown"))

        # 7. Validate genes
        genes = result.get("genes_detected", [])
        check("genes_detected has entries", len(genes) > 0)
        check("genes_detected are all ints",
              all(isinstance(g, int) for g in genes))

    finally:
        # 8. Shutdown
        print("\n🛑 Shutting down backend…")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server_proc.kill()

    # Summary
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
