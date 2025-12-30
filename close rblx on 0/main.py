import os
import psutil
import keyboard

def kill_roblox_player():
    """
    Terminates the process 'RobloxPlayerBeta.exe' if it is running.
    """
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'RobloxPlayerBeta.exe':
            try:
                process.terminate()
                print("[INFO] Process 'RobloxPlayerBeta.exe' terminated successfully.")
            except psutil.AccessDenied:
                print("[ERROR] Access denied when trying to terminate 'RobloxPlayerBeta.exe'.")
            except psutil.NoSuchProcess:
                print("[INFO] Process 'RobloxPlayerBeta.exe' is no longer running.")
            break
    else:
        print("[INFO] Process 'RobloxPlayerBeta.exe' not found.")

def main():
    """
    Watches for the key '0' and terminates the 'RobloxPlayerBeta.exe' process when detected.
    """
    print("[INFO] Script is now monitoring for the '0' key press...")
    print("Press 'Ctrl+C' to exit the script.")

    try:
        while True:
            if keyboard.is_pressed('0'):
                print("[INFO] '0' key detected.")
                kill_roblox_player()
    except KeyboardInterrupt:
        print("\n[INFO] Script terminated by user.")

if __name__ == "__main__":
    try:
        import psutil
        import keyboard
    except ImportError:
        print("[INFO] Missing dependencies. Installing them now...")
        os.system('pip install psutil keyboard')
        print("[INFO] Dependencies installed. Please re-run the script.")
        exit()

    main()
