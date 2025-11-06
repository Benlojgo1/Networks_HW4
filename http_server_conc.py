import sys
import socket
import os
import threading
import argparse
from datetime import datetime

# Glogal connection tracking
total_conn = 0
total_conn_lock = threading.Lock()
per_client_conn = {}
per_client_lock = threading.Lock()

CONTENT_TYPES = {
    ".html": "text/html",
    ".htm": "text/html",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".css": "text/css",
    ".js": "application/javascript",
    ".pdf": "application/pdf",
}

BUFFER_SIZE = 1024
FILE_CHUNK = 4096

# argument parsing
def parse_args():
    if len(sys.argv) != 7:
        print("Usage: ./http_server_conc -p <port> -maxclient <num> -maxtotal <num>")
        sys.exit(1)
    try:
        port_index = sys.argv.index("-p") + 1
        maxclient_index = sys.argv.index("-maxclient") + 1
        maxtotal_index = sys.argv.index("-maxtotal") + 1
        port = int(sys.argv[port_index])
        maxclient = int(sys.argv[maxclient_index])
        maxtotal = int(sys.argv[maxtotal_index])
    except (ValueError, IndexError):
        print("Invalid arguments.")
        sys.exit(1)
    return port, maxclient, maxtotal

# content type detection
def get_content_type(path):
    _, ext = os.path.splitext(path)
    return CONTENT_TYPES.get(ext.lower(), "application/octet-stream")

# URl decoder
def simple_unquote(s):
    res = ""
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            try:
                hex_val = s[i+1:i+3]
                res += chr(int(hex_val, 16))
                i += 3
            except ValueError:
                res += s[i]
                i += 1
        else:
            res += s[i]
            i += 1
    return res

# combine IP and User-Agent to get client ID
def make_client_id(addr, headers):
    user_agent = headers.get("User-Agent", "")
    return f"{addr[0]}::{user_agent}"

# connection slot tracking
def try_reserve_slot(client_id, maxclient, maxtotal):
    global total_conn
    with total_conn_lock:
        if total_conn >= maxtotal:
            return "total_limit"
        total_conn += 1

    with per_client_lock:
        count = per_client_conn.get(client_id, 0)
        if count >= maxclient:
            with total_conn_lock:
                total_conn -= 1
            return "client_limit"
        per_client_conn[client_id] = count + 1

    return "ok"


def release_slot(client_id):
    global total_conn
    with per_client_lock:
        if client_id in per_client_conn:
            per_client_conn[client_id] -= 1
            if per_client_conn[client_id] <= 0:
                del per_client_conn[client_id]

    with total_conn_lock:
        total_conn -= 1

# manually read headers
def read_headers(conn):
    conn.settimeout(2)
    data = b""
    try:
        while b"\r\n\r\n" not in data:
            part = conn.recv(BUFFER_SIZE)
            if not part:
                break
            data += part
    except socket.timeout:
        pass
    return data.decode("iso-8859-1", errors="replace")

# parse request line and headers
def parse_request_line_and_headers(request_text):
    lines = request_text.split("\r\n")
    if not lines or len(lines[0].split()) < 3:
        return None, None, None, {}

    method, path, version = lines[0].split()[:3]
    headers = {}
    for line in lines[1:]:
        if ": " in line:
            k, v = line.split(": ", 1)
            headers[k] = v
    return method, simple_unquote(path), version, headers

# client handler
def handle_client(conn, addr, maxclient, maxtotal):
    request_text = read_headers(conn)
    method, path, version, headers = parse_request_line_and_headers(request_text)

    client_id = make_client_id(addr, headers)
    result = try_reserve_slot(client_id, maxclient, maxtotal)

    if result == "total_limit":
        conn.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n")
        conn.close()
        return
    elif result == "client_limit":
        conn.sendall(b"HTTP/1.1 429 Too Many Requests\r\nContent-Length: 0\r\n\r\n")
        conn.close()
        return

    try:
        if not method or not path:
            conn.close()
            return

        if method != "GET":
            conn.sendall(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n")
            return

        safe_path = os.path.normpath(os.path.join(".", path.lstrip("/")))
        if not safe_path.startswith("."):
            conn.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
            return

        if os.path.isdir(safe_path):
            safe_path = os.path.join(safe_path, "index.html")

        if not os.path.exists(safe_path):
            conn.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
            return

        content_type = get_content_type(safe_path)
        file_size = os.path.getsize(safe_path)
        header = (
            "HTTP/1.1 200 OK\r\n"
            f"Date: {datetime.utcnow():%a, %d %b %Y %H:%M:%S GMT}\r\n"
            "Server: HTTPServerConcurrent/1.0\r\n"
            f"Content-Length: {file_size}\r\n"
            f"Content-Type: {content_type}\r\n"
            "Connection: close\r\n\r\n"
        )
        conn.sendall(header.encode())

        with open(safe_path, "rb") as f:
            while chunk := f.read(FILE_CHUNK):
                conn.sendall(chunk)

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        release_slot(client_id)
        conn.close()

# main method
def main():
    port, maxclient, maxtotal = parse_args()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", port))
    server_socket.listen(100)

    print(f"HTTP Server running on port {port}")
    print(f"Max per-client: {maxclient}, Max total: {maxtotal}")

    while True:
        conn, addr = server_socket.accept()
        t = threading.Thread(
            target=handle_client, args=(conn, addr, maxclient, maxtotal), daemon=True
        )
        t.start()


if __name__ == "__main__":
    main()
