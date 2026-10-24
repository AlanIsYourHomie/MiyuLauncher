from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JavaInstallation:
    executable: Path
    version: str | None
    major: int | None
    source: str


def _parse_java_version(output: str) -> tuple[str | None, int | None]:
    match = re.search(r'version\s+"([^"]+)"', output)
    if not match:
        match = re.search(r'openjdk\s+([0-9][^\s]*)', output, re.IGNORECASE)

    if not match:
        return None, None

    version = match.group(1)
    normalized = version.replace('_', '.')
    parts = normalized.split('.')

    try:
        if parts[0] == '1' and len(parts) > 1:
            major = int(parts[1])
        else:
            major = int(re.match(r'\d+', parts[0]).group())
    except (AttributeError, ValueError):
        major = None

    return version, major


def inspect_java(executable: Path) -> JavaInstallation | None:
    if not executable.exists():
        return None

    try:
        result = subprocess.run(
            [str(executable), '-version'],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None

    output = '\n'.join(part for part in (result.stdout, result.stderr) if part)
    version, major = _parse_java_version(output)

    return JavaInstallation(
        executable=executable.resolve(),
        version=version,
        major=major,
        source='detected',
    )


def _candidate_paths() -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []

    which_java = shutil.which('java')
    if which_java:
        candidates.append((Path(which_java), 'PATH'))

    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        candidates.append((Path(java_home) / 'bin' / 'java.exe', 'JAVA_HOME'))

    for env_name in ('ProgramFiles', 'ProgramFiles(x86)'):
        base = os.environ.get(env_name)
        if not base:
            continue

        base_path = Path(base)
        for root in (
            base_path / 'Java',
            base_path / 'Eclipse Adoptium',
            base_path / 'Microsoft',
            base_path / 'BellSoft',
            base_path / 'Amazon Corretto',
            base_path / 'Zulu',
        ):
            if not root.exists():
                continue

            for executable in root.glob('**/bin/java.exe'):
                candidates.append((executable, str(root)))

    return candidates


def find_java_installations() -> list[JavaInstallation]:
    found: list[JavaInstallation] = []
    seen: set[str] = set()

    for executable, source in _candidate_paths():
        try:
            key = str(executable.resolve()).lower()
        except OSError:
            key = str(executable).lower()

        if key in seen:
            continue
        seen.add(key)

        installation = inspect_java(executable)
        if installation is None:
            continue

        found.append(
            JavaInstallation(
                executable=installation.executable,
                version=installation.version,
                major=installation.major,
                source=source,
            )
        )

    return sorted(
        found,
        key=lambda item: (
            item.major is None,
            -(item.major or 0),
            str(item.executable).lower(),
        ),
    )


def select_java(preferred_major: int | None = None) -> JavaInstallation | None:
    installations = find_java_installations()

    if preferred_major is not None:
        for installation in installations:
            if installation.major == preferred_major:
                return installation

    return installations[0] if installations else None
