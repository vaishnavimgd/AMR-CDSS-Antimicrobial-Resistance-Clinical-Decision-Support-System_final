import os
import sys
import subprocess
import webbrowser
import time
import threading

def open_browser(port):
    """Waits for the server to start, then opens the browser."""
    time.sleep(2)  # Give Uvicorn 2 seconds to boot up
    url = f"http://127.0.0.1:{port}"
    print(f"Opening browser at: {url}")
    webbrowser.open(url)

def main():
    print("==================================================")
    print("   Starting AMR-CDSS System")
    print("==================================================")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")

    port = os.environ.get("PORT", "8000")

    # Start the browser thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start Uvicorn
    try:
        subprocess.run([
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
            "--reload" # useful for local dev, safe to keep
        ], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()