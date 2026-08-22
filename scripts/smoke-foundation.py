#!/usr/bin/env python3
"""Destructive, self-cleaning Memtly foundation smoke test.

Creates a temporary gallery, uploads a generated ordinary PNG through Memtly's
real chunk endpoint, completes the batch, and deletes the gallery. Credentials
come only from environment variables and are never printed.
"""

from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import re
import struct
import sys
import urllib.parse
import urllib.request
import uuid
import zlib

BASE_URL = os.environ.get("MEMTLY_SMOKE_BASE_URL", "").rstrip("/")
USERNAME = os.environ.get("MEMTLY_SMOKE_USERNAME", "")
PASSWORD = os.environ.get("MEMTLY_SMOKE_PASSWORD", "")


def require_environment() -> None:
    missing = [
        name
        for name, value in (
            ("MEMTLY_SMOKE_BASE_URL", BASE_URL),
            ("MEMTLY_SMOKE_USERNAME", USERNAME),
            ("MEMTLY_SMOKE_PASSWORD", PASSWORD),
        )
        if not value
    ]
    if missing:
        raise SystemExit("Missing required environment: " + ", ".join(missing))


def token_from(html: str) -> str:
    patterns = (
        r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
        r'value="([^"]+)"[^>]*name="__RequestVerificationToken"',
    )
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    raise RuntimeError("request verification token not found")


def generated_png(width: int = 16, height: int = 12) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend(((x * 17) % 256, (y * 23) % 256, ((x + y) * 11) % 256))
        rows.append(bytes(row))
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")


def multipart(fields: dict[str, str], file_field: tuple[str, str, str, bytes] | None = None) -> tuple[bytes, str]:
    boundary = "----memtly-smoke-" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(str(value).encode())
        body.extend(b"\r\n")
    if file_field:
        field, filename, content_type, payload = file_field
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(payload)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def main() -> int:
    require_environment()
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))

    with opener.open(BASE_URL + "/Account/Login", timeout=30) as response:
        login_html = response.read().decode(errors="replace")
    login_token = token_from(login_html)
    login_body = urllib.parse.urlencode(
        {
            "Username": USERNAME,
            "Password": PASSWORD,
            "__RequestVerificationToken": login_token,
        }
    ).encode()
    login_request = urllib.request.Request(
        BASE_URL + "/Account/Login",
        data=login_body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    with opener.open(login_request, timeout=30) as response:
        login = json.load(response)
    if login.get("success") is not True:
        raise RuntimeError("administrator login failed")

    with opener.open(BASE_URL + "/Account", timeout=30) as response:
        account_html = response.read().decode(errors="replace")
    request_token = token_from(account_html)

    suffix = uuid.uuid4().hex[:12]
    gallery_name = "Foundation Smoke " + suffix
    identifier = "foundation-smoke-" + suffix
    gallery_id: int | None = None

    try:
        add_body = urllib.parse.urlencode(
            {
                "Id": "0",
                "Identifier": identifier,
                "Name": gallery_name,
                "Type": "3",
                "SecretKey": "",
                "__RequestVerificationToken": request_token,
            }
        ).encode()
        add_request = urllib.request.Request(
            BASE_URL + "/Account/AddGallery",
            data=add_body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        with opener.open(add_request, timeout=30) as response:
            added = json.load(response)
        if added.get("success") is not True:
            raise RuntimeError("temporary gallery creation failed")

        query = urllib.parse.urlencode({"term": gallery_name, "type": "0", "page": "1", "limit": "10"})
        with opener.open(BASE_URL + "/Account/GalleriesList?" + query, timeout=30) as response:
            galleries_html = response.read().decode(errors="replace")
        row = re.search(
            rf'<tr[^>]*data-gallery-id="(\d+)"[^>]*data-gallery-identifier="{re.escape(identifier)}"',
            galleries_html,
        )
        if not row:
            raise RuntimeError("temporary gallery readback failed")
        gallery_id = int(row.group(1))

        payload = generated_png()
        request_id = str(uuid.uuid4())
        upload_id = str(uuid.uuid4())
        upload_fields = {
            "__RequestVerificationToken": request_token,
            "RequestId": request_id,
            "UploadId": upload_id,
            "CollectionId": "0",
            "GalleryId": str(gallery_id),
            "SecretKey": "",
            "FileSize": str(len(payload)),
            "FileChecksum": hashlib.sha256(payload).hexdigest(),
            "ChunkIndex": "0",
            "TotalChunks": "1",
        }
        upload_body, upload_type = multipart(
            upload_fields,
            ("File", "ordinary-smoke.png", "image/png", payload),
        )
        upload_request = urllib.request.Request(
            BASE_URL + "/Gallery/UploadFileChunk",
            data=upload_body,
            headers={"Content-Type": upload_type, "X-Requested-With": "XMLHttpRequest"},
        )
        with opener.open(upload_request, timeout=60) as response:
            uploaded = json.load(response)
        if uploaded.get("success") is not True or uploaded.get("complete") is not True:
            raise RuntimeError("ordinary PNG upload did not complete")

        complete_body, complete_type = multipart(
            {
                "RequestId": request_id,
                "CollectionId": "0",
                "GalleryId": str(gallery_id),
                "SecretKey": "",
                "UploadCount": "1",
            }
        )
        complete_request = urllib.request.Request(
            BASE_URL + "/Gallery/UploadCompleted",
            data=complete_body,
            headers={"Content-Type": complete_type, "X-Requested-With": "XMLHttpRequest"},
        )
        with opener.open(complete_request, timeout=30) as response:
            completed = json.load(response)
        if completed.get("success") is not True:
            raise RuntimeError("upload batch completion failed")

        print("login=passed")
        print("gallery_create_readback=passed")
        print("ordinary_png_upload=passed")
        print("upload_batch_complete=passed")
        return 0
    finally:
        if gallery_id is not None:
            delete_body = urllib.parse.urlencode(
                {
                    "id": str(gallery_id),
                    "__RequestVerificationToken": request_token,
                }
            ).encode()
            delete_request = urllib.request.Request(
                BASE_URL + "/Account/DeleteGallery",
                data=delete_body,
                method="DELETE",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            try:
                with opener.open(delete_request, timeout=30) as response:
                    deleted = json.load(response)
                print("cleanup=" + ("passed" if deleted.get("success") is True else "failed"))
            except Exception:
                print("cleanup=failed", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
