"""Offline importer for administrator-approved, data-only archive bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from core.event_store import record_event


class ImportRejected(ValueError):
    """Raised when an import fails policy or integrity checks."""


_PACKAGE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")
_ALLOWED_SUFFIXES = {".csv", ".json", ".md", ".txt"}
_MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
_MAX_FILE_BYTES = 16 * 1024 * 1024
_MAX_FILES = 256


class OfflineImporter:
    """Import a local ZIP only when its digest is pinned by a trusted local file."""

    def __init__(
        self,
        inbox: Path = Path("/var/lib/nexus-os/import/inbox"),
        destination: Path = Path("/var/lib/nexus-os/imported"),
        trusted_digests: Path = Path("/etc/nexus-os/trusted-imports.json"),
        event_writer: Callable[[str, dict[str, str]], int] = record_event,
    ) -> None:
        self.inbox = inbox.resolve()
        self.destination = destination.resolve()
        self.trusted_digests = trusted_digests
        self.event_writer = event_writer

    def import_archive(self, archive_name: str) -> dict[str, Any]:
        if Path(archive_name).name != archive_name or not archive_name.endswith(".zip"):
            raise ImportRejected("Supply the name of a .zip file in the import inbox.")

        archive = self.inbox / archive_name
        if archive.is_symlink() or not archive.is_file():
            raise ImportRejected("Archive is not a regular file in the import inbox.")

        try:
            trusted = json.loads(self.trusted_digests.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ImportRejected(f"Cannot read trusted import digests: {exc}") from exc
        if not isinstance(trusted, dict):
            raise ImportRejected("Trusted import digests must be a JSON object.")

        self.destination.mkdir(mode=0o750, parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".nexus-import-", dir=self.destination))
        try:
            snapshot = staging / "verified-input.zip"
            digest = self._snapshot_archive(archive, snapshot)
            package_id = trusted.get(digest)
            if not isinstance(package_id, str) or not _PACKAGE_ID.fullmatch(package_id):
                raise ImportRejected("Archive SHA-256 is not present in the trusted local manifest.")

            target = self.destination / package_id
            if target.exists():
                raise ImportRejected(f"Import destination already exists: {package_id}")

            extracted = staging / "files"
            extracted.mkdir(mode=0o700)
            total_size = self._extract_data_only(snapshot, extracted)
            snapshot.unlink()
            files = sorted(
                path.relative_to(extracted).as_posix()
                for path in extracted.rglob("*")
                if path.is_file()
            )
            os.replace(extracted, target)
            try:
                event_id = self.event_writer(
                    "import.completed",
                    {
                        "package": package_id,
                        "sha256": digest,
                        "file_count": str(len(files)),
                    },
                )
            except Exception as exc:
                try:
                    os.replace(target, extracted)
                except OSError as rollback_error:
                    raise ImportRejected(
                        f"Import stored at {target}, but event registration and rollback failed."
                    ) from rollback_error
                raise ImportRejected("Import aborted because the local event bus is unavailable.") from exc
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        staging.rmdir()

        return {
            "package": package_id,
            "sha256": digest,
            "files": files,
            "bytes": total_size,
            "executable": False,
            "event_id": event_id,
        }

    @staticmethod
    def _snapshot_archive(archive: Path, snapshot: Path) -> str:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(archive, flags)
        except OSError as exc:
            raise ImportRejected(f"Cannot safely open archive: {exc}") from exc

        digest = hashlib.sha256()
        total_size = 0
        try:
            with os.fdopen(descriptor, "rb") as source, snapshot.open("xb") as target:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise ImportRejected("Import source must be a regular file.")
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > _MAX_ARCHIVE_BYTES:
                        raise ImportRejected("Archive exceeds the 64 MiB import limit.")
                    digest.update(chunk)
                    target.write(chunk)
        except OSError as exc:
            raise ImportRejected(f"Cannot snapshot import archive: {exc}") from exc
        snapshot.chmod(0o600)
        return digest.hexdigest()

    @staticmethod
    def _extract_data_only(archive: Path, staging: Path) -> int:
        total_size = 0
        extracted = 0
        try:
            zip_file = zipfile.ZipFile(archive)
        except (OSError, zipfile.BadZipFile) as exc:
            raise ImportRejected(f"Invalid ZIP archive: {exc}") from exc

        with zip_file:
            for entry in zip_file.infolist():
                if entry.is_dir():
                    continue
                relative = PurePosixPath(entry.filename)
                mode = entry.external_attr >> 16
                if (
                    relative.is_absolute()
                    or not relative.parts
                    or any(part in {"", ".", ".."} for part in relative.parts)
                    or "\\" in entry.filename
                    or (mode & 0o170000) == 0o120000
                ):
                    raise ImportRejected(f"Unsafe archive path: {entry.filename!r}")
                if Path(relative.name).suffix.lower() not in _ALLOWED_SUFFIXES:
                    raise ImportRejected(f"Unsupported data-file type: {entry.filename!r}")
                if entry.file_size > _MAX_FILE_BYTES:
                    raise ImportRejected(f"File exceeds the 16 MiB limit: {entry.filename!r}")
                extracted += 1
                total_size += entry.file_size
                if extracted > _MAX_FILES or total_size > _MAX_ARCHIVE_BYTES:
                    raise ImportRejected("Archive exceeds the file-count or expanded-size limit.")

                destination = staging.joinpath(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zip_file.open(entry) as source, destination.open("xb") as output:
                    shutil.copyfileobj(source, output)
                destination.chmod(0o600)

        if extracted == 0:
            raise ImportRejected("Archive contains no supported data files.")
        return total_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="ZIP filename already placed in the local import inbox")
    args = parser.parse_args()
    try:
        result = OfflineImporter().import_archive(args.archive)
    except (ImportRejected, OSError) as exc:
        parser.exit(1, f"Import rejected: {exc}\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
