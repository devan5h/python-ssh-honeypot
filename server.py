import socket
import threading
import time
from database import init_db, log_to_db

HOST = "0.0.0.0"
PORT = 2222

init_db()

def receive_line(conn):
    data = b""
    while True:
        chunk = conn.recv(1024)
        if not chunk:
            break
        data += chunk
        if b"\n" in chunk:
            break
    return data.replace(b"\r", b"").replace(b"\n", b"").decode(errors="ignore").strip(" '\"\t")

def send_ssh_banner(conn):
    conn.sendall(b"SSH-2.0-OpenSSH_7.4p1 Ubuntu-10\r\n")
    time.sleep(0.3)

fake_fs = {
    "/home/admin": ["notes.txt", "backup.tar.gz", "secrets.log"],
    "/etc": ["passwd", "shadow", "hosts"],
    "/var/log": ["syslog", "auth.log"],
}

def handle_command(cmd, cwd):
    parts = cmd.split()

    if not parts:
        return "", cwd

    command = parts[0]

    # cd command
    if command == "cd":
        if len(parts) < 2:
            return "", cwd
        new_dir = parts[1]

        # absolute path
        if new_dir in fake_fs:
            return "", new_dir

        # relative path
        elif new_dir == "..":
            if cwd != "/home/admin":
                return "", cwd
            return "", "/home/admin"

        return "No such directory", cwd

    # ls command
    elif command == "ls":
        files = fake_fs.get(cwd, [])
        return "  ".join(files), cwd

    # pwd command
    elif command == "pwd":
        return cwd, cwd

    # whoami
    elif command == "whoami":
        return "root", cwd

    # uname
    elif command == "uname":
        return "Linux ubuntu 4.15.0-20-generic", cwd

    # cat command (fake restriction)
    elif command == "cat":
        if len(parts) > 1:
            filename = parts[1]
            if filename == "/etc/passwd":
                return "root:x:0:0:root:/root:/bin/bash", cwd
        return "Permission denied", cwd
        
    elif command == "exit":
        return "logout", "EXIT"

    return "command not found", cwd
    
def handle_client(conn, addr):
    try:
        ip = addr[0]
        print(f"[+] Connection from {ip}")

        send_ssh_banner(conn)

        # SSH-style login
        conn.sendall(b"login as: ")
        username = receive_line(conn)

        time.sleep(0.3)
        conn.sendall(b"Password: ")
        password = receive_line(conn)

        print(f"[DEBUG] {username}:{password}")
        log_to_db(ip, username, password)

        # Fake successful login
        cwd = "/home/admin"

        conn.sendall(b"\r\nWelcome to Ubuntu 18.04 LTS\r\n")
        conn.sendall(f"{cwd} $ ".encode())

        while True:
            cmd = receive_line(conn)

            if not cmd:
                break

            cmd = cmd.strip().lower()

            if cmd.startswith("$"):
                cmd = cmd[1:].strip()

            print(f"[CMD] {ip}: {cmd}")
            log_to_db(ip, cmd, "COMMAND")

            output, new_cwd = handle_command(cmd, cwd)
            
            time.sleep(0.2) 

            if new_cwd == "EXIT":
                conn.sendall(b"logout\r\n")
                break
            
            cwd = new_cwd

            if output:
                conn.sendall(output.encode() + b"\r\n")

            conn.sendall(f"{cwd} $ ".encode())
    except Exception as e:
        print(f"[-] Connection with {addr[0]} lost or closed.")
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[+] Honeypot running on port {PORT}")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()