import hupper
import os
import sys

def main():
    # Path to your main script you want to restart when the file changes
    script_path = "chat_web.py"

    if not os.path.exists(script_path):
        sys.stderr.write("Error: {} does not exist.\n".format(script_path))
        sys.exit(1)

    # Create a reloader and configure it to watch your main script
    reloader = hupper.start_reloader("watcher.main")
    reloader.watch_files([script_path])

    # Execute the main script
    globals = {"__file__": script_path, "__name__": "__main__"}
    exec(open(script_path).read(), globals)

if __name__ == "__main__":
    main()
