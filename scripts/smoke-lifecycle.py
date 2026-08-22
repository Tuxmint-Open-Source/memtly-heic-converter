#!/usr/bin/env python3
"""Self-cleaning Memtly media lifecycle regression smoke test.

Exercises ordinary supported media through Memtly's real HTTP endpoints without
printing credentials. The test creates a temporary gallery, uploads generated
JPEG/PNG/MP4/MOV fixtures, checks duplicate and raw-HEIC rejection, downloads the
gallery ZIP, and deletes the gallery.

Required environment:
  MEMTLY_SMOKE_BASE_URL
  MEMTLY_SMOKE_USERNAME
  MEMTLY_SMOKE_PASSWORD
"""

from __future__ import annotations

import hashlib
import http.cookiejar
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
import zlib
from dataclasses import dataclass
from collections.abc import Iterator
from pathlib import Path

BASE_URL = os.environ.get("MEMTLY_SMOKE_BASE_URL", "").rstrip("/")
USERNAME = os.environ.get("MEMTLY_SMOKE_USERNAME", "")
PASSWORD = os.environ.get("MEMTLY_SMOKE_PASSWORD", "")
MEDIA_FIXTURE_DIR = os.environ.get("MEMTLY_SMOKE_MEDIA_FIXTURE_DIR", "")
STRESS_IMAGES = int(os.environ.get("MEMTLY_SMOKE_STRESS_IMAGES", "0") or "0")
KEEP_GALLERY = os.environ.get("MEMTLY_SMOKE_KEEP_GALLERY", "").lower() in {"1", "true", "yes"}
EXISTING_GALLERY_ID = os.environ.get("MEMTLY_SMOKE_EXISTING_GALLERY_ID", "")
EXISTING_GALLERY_IDENTIFIER = os.environ.get("MEMTLY_SMOKE_EXISTING_GALLERY_IDENTIFIER", "")
EXISTING_GALLERY_SECRET_KEY = os.environ.get("MEMTLY_SMOKE_EXISTING_GALLERY_SECRET_KEY", "")
STATE_FILE = os.environ.get("MEMTLY_SMOKE_STATE_FILE", "")
CHUNK_SIZE = 10 * 1024 * 1024


@dataclass(frozen=True)
class MediaFixture:
    name: str
    content_type: str
    payload: bytes
    magic: bytes


def load_state_file() -> tuple[str, str, str]:
    if not STATE_FILE or not Path(STATE_FILE).exists():
        return "", "", ""
    data = json.loads(Path(STATE_FILE).read_text())
    return str(data.get("gallery_id", "")), str(data.get("gallery_identifier", "")), str(data.get("gallery_secret_key", ""))


def save_state_file(gallery_id: int, identifier: str, secret_key: str) -> None:
    if not STATE_FILE:
        return
    Path(STATE_FILE).write_text(json.dumps({"gallery_id": gallery_id, "gallery_identifier": identifier, "gallery_secret_key": secret_key}))


def remove_state_file() -> None:
    if STATE_FILE and Path(STATE_FILE).exists():
        Path(STATE_FILE).unlink()


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
    for pattern in (
        r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
        r'value="([^"]+)"[^>]*name="__RequestVerificationToken"',
    ):
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    raise RuntimeError("request verification token not found")


def png_bytes(width: int = 16, height: int = 12, seed: int = 0) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend((((x * 17) + seed) % 256, ((y * 23) + seed) % 256, ((x + y + seed) * 11) % 256))
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")


def jpeg_bytes() -> bytes:
    # 1x1 black JPEG generated once from a simple test image. It contains no EXIF/XMP metadata.
    return bytes.fromhex(
        "ffd8ffe000104a46494600010101006000600000ffdb0043000302020302020303030304030304050805050404050a070706080c0a0c0c0b0a0b0b0d0e12100d0e110e0b0b1016101113141515150c0f171816141812141514ffdb00430103040405040509050509140d0b0d141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414ffc00011080001000103012200021101031101ffc4001400010000000000000000000000000000000000000008ffc4001410010000000000000000000000000000000000000000ffda000c03010002110311003f00b2c001ffd9"
    )


def make_video(path: Path, fmt: str) -> bytes:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required for MP4/MOV lifecycle fixtures")
    args = [
        "ffmpeg",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=16x16:d=0.2:r=1",
        "-an",
        "-frames:v",
        "1",
        "-c:v",
        "mpeg4",
        "-pix_fmt",
        "yuv420p",
    ]
    if fmt == "mp4":
        args += ["-movflags", "+faststart", "-f", "mp4"]
    else:
        args += ["-f", "mov"]
    args.append(str(path))
    subprocess.run(args, check=True)
    return path.read_bytes()


def fixtures() -> Iterator[MediaFixture]:
    if MEDIA_FIXTURE_DIR:
        fixture_dir = Path(MEDIA_FIXTURE_DIR)
        yield MediaFixture("ordinary.jpg", "image/jpeg", (fixture_dir / "ordinary.jpg").read_bytes(), b"\xff\xd8\xff")
        yield MediaFixture("ordinary.png", "image/png", (fixture_dir / "ordinary.png").read_bytes(), b"\x89PNG")
        yield MediaFixture("ordinary-large.png", "image/png", (fixture_dir / "ordinary-large.png").read_bytes(), b"\x89PNG")
        yield MediaFixture("ordinary.mp4", "video/mp4", (fixture_dir / "ordinary.mp4").read_bytes(), b"")
        yield MediaFixture("ordinary.mov", "video/quicktime", (fixture_dir / "ordinary.mov").read_bytes(), b"")
        for index in range(STRESS_IMAGES):
            yield MediaFixture(f"stress-{index + 1:03d}.png", "image/png", png_bytes(seed=index + 1), b"\x89PNG")
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        yield MediaFixture("ordinary.jpg", "image/jpeg", jpeg_bytes(), b"\xff\xd8\xff")
        yield MediaFixture("ordinary.png", "image/png", png_bytes(), b"\x89PNG")
        yield MediaFixture("ordinary-large.png", "image/png", png_bytes() + (b"\0" * (CHUNK_SIZE + 128)), b"\x89PNG")
        yield MediaFixture("ordinary.mp4", "video/mp4", make_video(tmpdir / "ordinary.mp4", "mp4"), b"")
        yield MediaFixture("ordinary.mov", "video/quicktime", make_video(tmpdir / "ordinary.mov", "mov"), b"")
        for index in range(STRESS_IMAGES):
            yield MediaFixture(f"stress-{index + 1:03d}.png", "image/png", png_bytes(seed=index + 1), b"\x89PNG")


def multipart(fields: dict[str, str], file_field: tuple[str, str, str, bytes] | None = None) -> tuple[bytes, str]:
    boundary = "----memtly-lifecycle-" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(str(value).encode())
        body.extend(b"\r\n")
    if file_field:
        field, filename, content_type, payload = file_field
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode())
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(payload)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


class Session:
    def __init__(self) -> None:
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.token = ""

    def open(self, path: str, **kwargs):
        return self.opener.open(BASE_URL + path, **kwargs)

    def post_form(self, path: str, fields: dict[str, str], *, method: str | None = None):
        body = urllib.parse.urlencode(fields).encode()
        req = urllib.request.Request(
            BASE_URL + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest"},
        )
        with self.opener.open(req, timeout=60) as response:
            return json.load(response)

    def login(self) -> None:
        with self.open("/Account/Login", timeout=30) as response:
            html = response.read().decode(errors="replace")
        self.token = token_from(html)
        result = self.post_form("/Account/Login", {"Username": USERNAME, "Password": PASSWORD, "__RequestVerificationToken": self.token})
        if result.get("success") is not True:
            raise RuntimeError("administrator login failed")
        with self.open("/Account", timeout=30) as response:
            account_html = response.read().decode(errors="replace")
            if "/Account/Login" in response.geturl() or "logout" not in account_html.lower():
                raise RuntimeError("authenticated account page did not load")

    def create_gallery(self) -> tuple[int, str, str]:
        suffix = uuid.uuid4().hex[:12]
        name = "Lifecycle Smoke " + suffix
        identifier = "lifecycle-smoke-" + suffix
        secret_key = "lifecycle-" + uuid.uuid4().hex
        result = self.post_form(
            "/Account/AddGallery",
            {"Id": "0", "Identifier": identifier, "Name": name, "Type": "1", "SecretKey": secret_key, "__RequestVerificationToken": self.token},
        )
        if result.get("success") is not True:
            raise RuntimeError("temporary gallery creation failed")
        query = urllib.parse.urlencode({"term": name, "type": "0", "page": "1", "limit": "10"})
        with self.open("/Account/GalleriesList?" + query, timeout=30) as response:
            html = response.read().decode(errors="replace")
        for row in re.findall(r'<tr[^>]*data-gallery-id="\d+"[^>]*>', html, re.I):
            attrs = dict(re.findall(r'data-gallery-([\w-]+)="([^"]*)"', row, re.I))
            if attrs.get("name") == name:
                return int(attrs["id"]), attrs["identifier"], secret_key
        raise RuntimeError("temporary gallery readback failed")

    def gallery_token(self, identifier: str) -> str:
        with self.open("/Gallery?" + urllib.parse.urlencode({"identifier": identifier}), timeout=30) as response:
            html = response.read().decode(errors="replace")
        self.token = token_from(html)
        return self.token

    def upload(self, gallery_id: int, item: MediaFixture, *, secret_key: str = "", duplicate_checksum: str | None = None) -> dict:
        checksum = duplicate_checksum or hashlib.sha256(item.payload).hexdigest()
        request_id = str(uuid.uuid4())
        upload_id = str(uuid.uuid4())
        responses = []
        total_chunks = (len(item.payload) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for chunk_index in range(total_chunks):
            start = chunk_index * CHUNK_SIZE
            chunk = item.payload[start : start + CHUNK_SIZE]
            body, content_type = multipart(
                {
                    "__RequestVerificationToken": self.token,
                    "RequestId": request_id,
                    "UploadId": upload_id,
                    "CollectionId": "0",
                    "GalleryId": str(gallery_id),
                    "SecretKey": secret_key,
                    "FileSize": str(len(item.payload)),
                    "FileChecksum": checksum,
                    "ChunkIndex": str(chunk_index),
                    "TotalChunks": str(total_chunks),
                },
                ("File", item.name, item.content_type, chunk),
            )
            req = urllib.request.Request(BASE_URL + "/Gallery/UploadFileChunk", data=body, headers={"Content-Type": content_type, "X-Requested-With": "XMLHttpRequest"})
            try:
                with self.opener.open(req, timeout=90) as response:
                    responses.append(json.load(response))
            except urllib.error.HTTPError as error:
                responses.append(json.loads(error.read().decode(errors="replace")))
                break
        return responses[-1]

    def complete(self, gallery_id: int, count: int, *, secret_key: str = "") -> dict:
        body, content_type = multipart({"RequestId": str(uuid.uuid4()), "CollectionId": "0", "GalleryId": str(gallery_id), "SecretKey": secret_key, "UploadCount": str(count)})
        req = urllib.request.Request(BASE_URL + "/Gallery/UploadCompleted", data=body, headers={"Content-Type": content_type, "X-Requested-With": "XMLHttpRequest"})
        with self.opener.open(req, timeout=60) as response:
            return json.load(response)

    def gallery_html(self, identifier: str) -> str:
        with self.open("/Gallery?" + urllib.parse.urlencode({"identifier": identifier}), timeout=30) as response:
            return response.read().decode(errors="replace")

    def download_zip(self, gallery_id: int, *, secret_key: str = "") -> bytes:
        body = urllib.parse.urlencode({"id": str(gallery_id), "secretKey": secret_key, "group": "0|All|All", "__RequestVerificationToken": self.token}).encode()
        req = urllib.request.Request(BASE_URL + "/Gallery/DownloadGallery", data=body, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        with self.opener.open(req, timeout=120) as response:
            return response.read()

    def validate_gallery_media(self, gallery_id: int, identifier: str, *, secret_key: str = "") -> None:
        html = self.gallery_html(identifier)
        if "__RequestVerificationToken" not in html:
            raise RuntimeError("gallery page did not render the expected Memtly gallery token")
        print("gallery_render=passed")

        if not secret_key:
            match = re.search(r'data-gallery-key="([^"]*)"', html)
            if match:
                secret_key = match.group(1)

        payload = self.download_zip(gallery_id, secret_key=secret_key)
        if not payload.startswith(b"PK\x03\x04"):
            raise RuntimeError("gallery download did not return a zip")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = [Path(name).name.lower() for name in archive.namelist()]
            for ext in (".jpg", ".png", ".mp4", ".mov"):
                if not any(name.endswith(ext) for name in names):
                    raise RuntimeError(f"download zip missing {ext}")
            if any(name.endswith((".heic", ".heif")) for name in names):
                raise RuntimeError("download zip contained raw HEIC/HEIF")
        print("download_zip=passed")

    def delete_gallery(self, gallery_id: int) -> bool:
        result = self.post_form("/Account/DeleteGallery", {"id": str(gallery_id), "__RequestVerificationToken": self.token}, method="DELETE")
        return result.get("success") is True


def main() -> int:
    require_environment()
    session = Session()
    session.login()
    print("login=passed")

    existing_gallery_id = EXISTING_GALLERY_ID
    existing_gallery_identifier = EXISTING_GALLERY_IDENTIFIER
    existing_gallery_secret_key = EXISTING_GALLERY_SECRET_KEY
    if STATE_FILE and (not existing_gallery_id or not existing_gallery_identifier):
        existing_gallery_id, existing_gallery_identifier, existing_gallery_secret_key = load_state_file()

    if existing_gallery_id and existing_gallery_identifier:
        session.gallery_token(existing_gallery_identifier)
        session.validate_gallery_media(int(existing_gallery_id), existing_gallery_identifier, secret_key=existing_gallery_secret_key)
        print("existing_gallery_validation=passed")
        if not KEEP_GALLERY:
            if session.delete_gallery(int(existing_gallery_id)):
                remove_state_file()
                print("cleanup=passed")
            else:
                print("cleanup=failed", file=sys.stderr)
        return 0

    gallery_id, identifier, secret_key = session.create_gallery()
    print("gallery_create_readback=passed")
    print(f"gallery_id={gallery_id}")
    print(f"gallery_identifier={identifier}")
    print(f"gallery_secret_key_present={str(bool(secret_key)).lower()}")
    save_state_file(gallery_id, identifier, secret_key)
    try:
        session.gallery_token(identifier)
        uploaded: list[MediaFixture] = []
        generated = list(fixtures())
        chunked_upload_seen = False
        for item in generated:
            if len(item.payload) > CHUNK_SIZE:
                chunked_upload_seen = True
            result = session.upload(gallery_id, item, secret_key=secret_key)
            if result.get("success") is not True or result.get("complete") is not True:
                raise RuntimeError(f"{item.name} did not complete upload: {result}")
            uploaded.append(item)
        print("ordinary_media_uploads=passed")
        print(f"uploaded_count={len(uploaded)}")
        if chunked_upload_seen:
            print("chunked_upload=passed")
        if STRESS_IMAGES:
            print(f"stress_images=passed count={STRESS_IMAGES}")
        complete = session.complete(gallery_id, len(uploaded), secret_key=secret_key)
        if complete.get("success") is not True:
            raise RuntimeError("batch completion failed")
        print("upload_batch_complete=passed")

        duplicate = session.upload(gallery_id, uploaded[0], secret_key=secret_key)
        if duplicate.get("success") is not False:
            raise RuntimeError("duplicate upload was not rejected")
        print("duplicate_rejection=passed")

        raw_heic = MediaFixture("raw.heic", "image/heic", b"\x00\x00\x00\x10ftypheic", b"")
        raw = session.upload(gallery_id, raw_heic, secret_key=secret_key)
        if raw.get("success") is not False:
            raise RuntimeError("raw HEIC server upload was not rejected")
        print("raw_heic_server_rejection=passed")

        session.validate_gallery_media(gallery_id, identifier, secret_key=secret_key)
        return 0
    finally:
        if KEEP_GALLERY:
            print("cleanup=skipped keep_gallery=true")
        elif session.delete_gallery(gallery_id):
            print("cleanup=passed")
        else:
            print("cleanup=failed", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
