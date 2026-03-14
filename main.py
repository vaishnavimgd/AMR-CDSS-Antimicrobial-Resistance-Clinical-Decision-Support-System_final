import os
import sys
import subprocess

def main():
    print("==================================================")
    print("   Starting AMR-CDSS System")
    print("==================================================")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")

    port = os.environ.get("PORT", "8000")

    subprocess.run([
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        port
    ], cwd=backend_dir)

if __name__ == "__main__":
    main()