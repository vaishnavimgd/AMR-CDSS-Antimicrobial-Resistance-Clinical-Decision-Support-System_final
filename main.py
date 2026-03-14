import os
import sys
import time
import webbrowser
import subprocess

def main():
    print("==================================================")
    print("   Starting AMR-CDSS System                       ")
    print("==================================================")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    
    # 1. Start the FastAPI backend server as a separate process
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir
    )
    
    # Wait a moment for the server to boot up
    time.sleep(2.5)
    
    # 2. Automatically open the browser to the dashboard
    dashboard_url = "http://127.0.0.1:8000/"
    print(f"\nOpening AMR Dashboard at {dashboard_url}\n")
    webbrowser.open(dashboard_url)
    
    try:
        # Keep the main process alive until the user stops it (Ctrl+C)
        server_process.wait()
    except KeyboardInterrupt:
        print("\n[!] Shutting down AMR-CDSS System...")
        server_process.terminate()

if __name__ == "__main__":
    main()
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)