"""Minimal Redis RESP stub for local smoke tests."""

from __future__ import annotations

import argparse
import asyncio
from typing import Dict, Optional, Tuple


class Store:
    def __init__(self) -> None:
        self.data: Dict[str, str] = {}
        self.hashes: Dict[str, Dict[str, str]] = {}

    def get(self, key: str) -> Optional[str]:
        return self.data.get(key)

    def set(self, key: str, value: str) -> None:
        self.data[key] = value

    def incrbyfloat(self, key: str, amount: float) -> float:
        cur = float(self.data.get(key, "0") or 0)
        cur += amount
        self.data[key] = str(cur)
        return cur


def encode_simple(s: str) -> bytes:
    return f"+{s}\r\n".encode()


def encode_bulk(s: Optional[str]) -> bytes:
    if s is None:
        return b"$-1\r\n"
    b = s.encode()
    return f"${len(b)}\r\n".encode() + b + b"\r\n"


def encode_int(n: int) -> bytes:
    return f":{n}\r\n".encode()


def encode_err(s: str) -> bytes:
    return f"-ERR {s}\r\n".encode()


def parse_commands(buf: bytearray) -> Tuple[list[list[str]], int]:
    cmds: list[list[str]] = []
    i = 0
    while True:
        if i >= len(buf) or buf[i] != ord("*"):
            break
        cr = buf.find(b"\r\n", i)
        if cr < 0:
            break
        try:
            n = int(buf[i + 1 : cr])
        except ValueError:
            break
        j = cr + 2
        args: list[str] = []
        ok = True
        for _ in range(n):
            if j >= len(buf) or buf[j] != ord("$"):
                ok = False
                break
            cr2 = buf.find(b"\r\n", j)
            if cr2 < 0:
                ok = False
                break
            try:
                ln = int(buf[j + 1 : cr2])
            except ValueError:
                ok = False
                break
            start = cr2 + 2
            end = start + ln
            if end + 2 > len(buf):
                ok = False
                break
            args.append(buf[start:end].decode("utf-8", errors="replace"))
            j = end + 2
        if not ok:
            break
        cmds.append(args)
        i = j
    return cmds, i


def dispatch(store: Store, args: list[str]) -> bytes:
    if not args:
        return encode_err("empty")
    op = args[0].upper()
    if op == "PING":
        return encode_simple("PONG")
    if op == "GET" and len(args) >= 2:
        return encode_bulk(store.get(args[1]))
    if op == "SET" and len(args) >= 3:
        store.set(args[1], args[2])
        return encode_simple("OK")
    if op == "SELECT":
        return encode_simple("OK")
    if op in ("CLIENT", "HELLO", "INFO", "CONFIG", "COMMAND", "MODULE"):
        return encode_simple("OK")
    if op == "INCRBYFLOAT" and len(args) >= 3:
        val = store.incrbyfloat(args[1], float(args[2]))
        return encode_bulk(str(val))
    if op == "EVAL":
        # Always allow token-bucket for smoke (return 1)
        return encode_int(1)
    if op == "HMGET":
        # return array of null bulks
        n = max(0, len(args) - 2)
        out = f"*{n}\r\n".encode()
        for _ in range(n):
            out += encode_bulk(None)
        return out
    if op == "HMSET":
        return encode_simple("OK")
    if op == "EXPIRE":
        return encode_int(1)
    return encode_simple("OK")


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, store: Store) -> None:
    buf = bytearray()
    try:
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            buf.extend(chunk)
            cmds, consumed = parse_commands(buf)
            if consumed:
                del buf[:consumed]
            for args in cmds:
                writer.write(dispatch(store, args))
                await writer.drain()
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass


async def main(host: str, port: int) -> None:
    store = Store()

    async def _client(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
        await handle(r, w, store)

    server = await asyncio.start_server(_client, host, port)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets or [])
    print(f"resp-stub listening on {addrs}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=6379)
    args = p.parse_args()
    asyncio.run(main(args.host, args.port))
