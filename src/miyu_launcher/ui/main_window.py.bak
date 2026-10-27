from __future__ import annotations

import re
import subprocess
from threading import Event

from PySide6.QtCore import Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from miyu_launcher.core.game_launcher import LaunchCancelled, launch_minecraft
from miyu_launcher.core.java import find_java_installations, select_java
from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion, find_default_minecraft_installation
from miyu_launcher.core.paths import get_launcher_paths
from miyu_launcher.core.system import get_system_info
from miyu_launcher.core.version_resolver import resolve_version


def _natural_version_key(version_id: str) -> tuple[tuple[int, object], ...]:
    parts = re.split(r"(\d+)", version_id.casefold())
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in parts if part)


def _ordered_launchable_versions(installation: MinecraftInstallation) -> list[MinecraftVersion]:
    versions = [item for item in installation.versions if item.has_modern_arguments]
    releases = sorted(
        (item for item in versions if item.version_type == "release"),
        key=lambda item: _natural_version_key(item.version_id),
        reverse=True,
    )
    other_versions = sorted(
        (item for item in versions if item.version_type != "release"),
        key=lambda item: _natural_version_key(item.version_id),
        reverse=True,
    )
    return releases + other_versions


class _LaunchWorker(QThread):
    progress = Signal(str)
    authentication_code = Signal(str, str, str)
    launched = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, version_id: str, parent=None) -> None:
        super().__init__(parent)
        self.version_id = version_id
        self.cancel_event = Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            process = launch_minecraft(
                self.version_id,
                progress=self.progress.emit,
                authentication_code=self.authentication_code.emit,
                cancel_event=self.cancel_event,
            )
        except LaunchCancelled:
            self.cancelled.emit()
            return
        except Exception as exc:  # Errors are surfaced in the UI, without logging tokens.
            self.failed.emit(str(exc) or exc.__class__.__name__)
            return
        self.launched.emit(process)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("MiyuLauncher")
        self.resize(1000, 640)

        self._launch_worker: _LaunchWorker | None = None
        self._game_process: subprocess.Popen | None = None
        self._close_when_idle = False
        self._installation = find_default_minecraft_installation()
        self._versions: dict[str, MinecraftVersion] = {}

        system_info = get_system_info()
        launcher_paths = get_launcher_paths()
        launcher_paths.create()
        java_installations = find_java_installations()
        selected_java = select_java()

        title = QLabel("MiyuLauncher")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: 650;")

        subtitle = QLabel("Tu Minecraft, preparado desde un solo lugar")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ram = (
            f"{system_info.total_ram_gb} GB"
            if system_info.total_ram_gb is not None
            else "No disponible"
        )
        system_label = QLabel(
            f"Sistema: {system_info.operating_system} {system_info.release}  ·  "
            f"Arquitectura: {system_info.architecture}  ·  RAM: {ram}\n"
            f"Datos del launcher: {launcher_paths.root}"
        )
        system_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        system_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if selected_java is not None:
            java_version = selected_java.version or "desconocida"
            java_major = selected_java.major if selected_java.major is not None else "?"
            java_text = (
                f"Java detectado: {java_version} (major {java_major})  ·  "
                f"Instalaciones encontradas: {len(java_installations)}"
            )
        else:
            java_text = "Java del sistema no detectado; MiyuLauncher lo preparará cuando sea necesario."
        self.java_label = QLabel(java_text)
        self.java_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.java_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.java_label.setWordWrap(True)

        version_title = QLabel("VERSIÓN DE MINECRAFT")
        version_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_title.setStyleSheet("font-weight: 600; letter-spacing: 1px;")

        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(280)
        self.version_combo.setToolTip("Selecciona una versión instalada de Minecraft Java Edition.")

        self.version_detail = QLabel()
        self.version_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_detail.setWordWrap(True)

        self.play_button = QPushButton("JUGAR")
        self.play_button.setFixedSize(220, 48)
        self.play_button.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.play_button.clicked.connect(self._start_launch)
        self.cancel_button = QPushButton("CANCELAR")
        self.cancel_button.setFixedHeight(42)
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self._cancel_launch)

        play_row = QHBoxLayout()
        play_row.addStretch()
        play_row.addWidget(self.play_button)
        play_row.addWidget(self.cancel_button)
        play_row.addStretch()

        version_row = QHBoxLayout()
        version_row.addStretch()
        version_row.addWidget(self.version_combo)
        version_row.addStretch()

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(28)

        self.authentication_code_label = QLabel()
        self.authentication_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.authentication_code_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.authentication_code_label.setWordWrap(True)
        self.authentication_code_label.hide()

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumWidth(420)
        self.progress_bar.hide()

        self._process_timer = QTimer(self)
        self._process_timer.setInterval(1500)
        self._process_timer.timeout.connect(self._poll_game_process)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(system_label)
        layout.addWidget(self.java_label)
        layout.addSpacing(16)
        layout.addWidget(version_title)
        layout.addLayout(version_row)
        layout.addWidget(self.version_detail)
        layout.addSpacing(12)
        layout.addLayout(play_row)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addWidget(self.authentication_code_label)
        layout.addStretch(1)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.version_combo.currentIndexChanged.connect(self._on_version_changed)
        self._populate_versions()

    def _populate_versions(self) -> None:
        self.version_combo.clear()
        self._versions.clear()

        if self._installation is not None:
            for version in _ordered_launchable_versions(self._installation):
                self._versions[version.version_id] = version
                label = version.version_id
                if version.version_type == "snapshot":
                    label += "  · snapshot"
                self.version_combo.addItem(label, userData=version.version_id)

        has_versions = self.version_combo.count() > 0
        self.version_combo.setEnabled(has_versions)
        self.play_button.setEnabled(has_versions)

        if not has_versions:
            if self._installation is None:
                self.status_label.setText(
                    "No se encontró una instalación estándar de Minecraft. Instala Minecraft Java Edition primero."
                )
            else:
                self.status_label.setText(
                    "No hay versiones instaladas con el formato de lanzamiento compatible todavía."
                )
            self.version_detail.setText("")
            return

        self._on_version_changed()
        self.status_label.setText("Listo para jugar. La primera preparación puede tardar un poco.")

    def _on_version_changed(self, *_args) -> None:
        version_id = self.version_combo.currentData()
        version = self._versions.get(version_id) if version_id else None
        if version is None:
            self.version_detail.setText("")
            return

        required_java = version.java_major_version
        try:
            resolved = resolve_version(self._installation, version) if self._installation else None
        except Exception:
            resolved = None

        if resolved is not None and resolved.java_compatible and resolved.java is not None:
            java_text = f"Java {resolved.java.major} disponible"
        elif required_java is not None:
            java_text = f"Necesita Java {required_java}; MiyuLauncher comprobará o instalará el runtime automáticamente"
        else:
            java_text = "Java se comprobará al iniciar"

        kind = "Snapshot" if version.version_type == "snapshot" else "Release"
        self.version_detail.setText(f"{kind}  ·  {java_text}")

    def _start_launch(self) -> None:
        if self._launch_worker is not None and self._launch_worker.isRunning():
            return
        if self._game_process is not None and self._game_process.poll() is None:
            return

        version_id = self.version_combo.currentData()
        if not version_id:
            QMessageBox.warning(self, "Versión no disponible", "Selecciona una versión de Minecraft.")
            return

        self.authentication_code_label.clear()
        self.authentication_code_label.hide()
        self.play_button.setEnabled(False)
        self.version_combo.setEnabled(False)
        self.play_button.setText("PREPARANDO...")
        self.status_label.setText(f"Preparando Minecraft {version_id}...")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.cancel_button.setEnabled(True)
        self.cancel_button.show()

        worker = _LaunchWorker(version_id, self)
        self._launch_worker = worker
        worker.progress.connect(self._on_launch_progress)
        worker.authentication_code.connect(self._show_authentication_code)
        worker.launched.connect(self._on_game_launched)
        worker.failed.connect(self._on_launch_failed)
        worker.cancelled.connect(self._on_launch_cancelled)
        worker.finished.connect(self._on_worker_finished)
        worker.start()

    def _on_launch_progress(self, message: str) -> None:
        worker = self._launch_worker
        if worker is not None and worker.cancel_event.is_set():
            return
        self.status_label.setText(message)

    def _cancel_launch(self) -> None:
        worker = self._launch_worker
        if worker is None or not worker.isRunning():
            return
        worker.cancel()
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Cancelando el lanzamiento; se completará la operación actual de forma segura...")

    def _show_authentication_code(self, verification_url: str, user_code: str, message: str) -> None:
        self.authentication_code_label.setText(
            f"Inicia sesión con la cuenta que tiene Minecraft: Java Edition.\n"
            f"Código: {user_code}\n"
            f"Enlace: {verification_url}\n"
            "El código es temporal y solo sirve para esta sesión."
        )
        self.authentication_code_label.show()
        opened = QDesktopServices.openUrl(QUrl(verification_url))
        if opened:
            self.status_label.setText("Se abrió el navegador. Introduce el código mostrado abajo y completa el inicio de sesión.")
        else:
            self.status_label.setText("Abre el enlace de Microsoft e introduce el código mostrado abajo.")

    def _on_game_launched(self, process: subprocess.Popen) -> None:
        self._game_process = process
        self.cancel_button.hide()
        self.play_button.setText("MINECRAFT EN EJECUCIÓN")
        self.play_button.setEnabled(False)
        self.version_combo.setEnabled(False)
        self.progress_bar.hide()
        self.status_label.setText(f"Minecraft se inició correctamente (PID {process.pid}).")
        self._process_timer.start()

    def _on_launch_failed(self, message: str) -> None:
        self.progress_bar.hide()
        self.status_label.setText("No se pudo iniciar Minecraft.")
        self.authentication_code_label.hide()
        self.cancel_button.hide()
        QMessageBox.critical(self, "Error al iniciar Minecraft", message)
        self.play_button.setText("JUGAR")
        self.play_button.setEnabled(self.version_combo.count() > 0)
        self.version_combo.setEnabled(self.version_combo.count() > 0)

    def _on_launch_cancelled(self) -> None:
        self.progress_bar.hide()
        self.authentication_code_label.hide()
        self.status_label.setText("Lanzamiento cancelado. No se inició Minecraft.")

    def _on_worker_finished(self) -> None:
        worker = self._launch_worker
        self._launch_worker = None
        if worker is not None:
            worker.deleteLater()

        if self._game_process is None:
            self.progress_bar.hide()
            self.cancel_button.hide()
            self.cancel_button.setEnabled(True)
            self.play_button.setText("JUGAR")
            self.play_button.setEnabled(self.version_combo.count() > 0)
            self.version_combo.setEnabled(self.version_combo.count() > 0)
        if self._close_when_idle:
            QTimer.singleShot(0, self.close)

    def _poll_game_process(self) -> None:
        process = self._game_process
        if process is None:
            self._process_timer.stop()
            return

        return_code = process.poll()
        if return_code is None:
            return

        self._process_timer.stop()
        self._game_process = None
        self.play_button.setText("JUGAR")
        self.play_button.setEnabled(self.version_combo.count() > 0)
        self.version_combo.setEnabled(self.version_combo.count() > 0)
        self.authentication_code_label.hide()
        self.cancel_button.hide()

        if return_code == 0:
            self.status_label.setText("Minecraft se cerró correctamente.")
        else:
            self.status_label.setText(
                f"Minecraft terminó con código {return_code}. Si fue inesperado, revisa logs/latest.log."
            )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override name
        worker = self._launch_worker
        if worker is not None and worker.isRunning():
            self._close_when_idle = True
            self._cancel_launch()
            event.ignore()
            return
        event.accept()
