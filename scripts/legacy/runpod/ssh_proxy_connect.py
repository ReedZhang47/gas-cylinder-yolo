"""OpenSSH ProxyCommand: forward a raw TCP stream through Clash HTTP CONNECT."""

from __future__ import annotations

import os
import socket
import sys
import threading


def main() -> None:
    host, port, proxy_host, proxy_port = sys.argv[1:5]
    if os.name == "nt":
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    connection = socket.create_connection((proxy_host, int(proxy_port)), timeout=20)
    request = (
        f"CONNECT {host}:{port} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Proxy-Connection: Keep-Alive\r\n\r\n"
    )
    connection.sendall(request.encode("ascii"))
    header = bytearray()
    while not header.endswith(b"\r\n\r\n"):
        chunk = connection.recv(1)
        if not chunk or len(header) > 65536:
            raise RuntimeError("Proxy closed or sent an oversized response")
        header.extend(chunk)
    status = header.split(b"\r\n", 1)[0]
    if b" 200 " not in status:
        raise RuntimeError(f"Proxy CONNECT failed: {status.decode('latin-1')}")
    connection.settimeout(None)

    def from_stdin() -> None:
        try:
            while data := os.read(sys.stdin.fileno(), 65536):
                connection.sendall(data)
        except (OSError, ValueError):
            pass
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass

    threading.Thread(target=from_stdin, daemon=True).start()
    try:
        while data := connection.recv(65536):
            os.write(sys.stdout.fileno(), data)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
