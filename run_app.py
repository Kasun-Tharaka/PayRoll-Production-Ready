import streamlit.web.cli as stcli
import os
import sys
import webbrowser
import threading
import time

def resolve_path(path):
    basedir = getattr(sys, '_MEIPASS', os.getcwd())
    return os.path.join(basedir, path)

def open_browser():
    # Wait 2 seconds for the Streamlit server to boot up, then open the browser
    time.sleep(2)
    webbrowser.open_new("http://localhost:8501")

if __name__ == "__main__":
    # Start the browser thread
    threading.Thread(target=open_browser).start()

    # Launch Streamlit (Headless is set to true to prevent double tabs)
    args = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--server.headless", "true", 
        "--global.developmentMode", "false",
    ]
    sys.argv = args
    sys.exit(stcli.main())