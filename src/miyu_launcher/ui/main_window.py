from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from miyu_launcher.core.java import find_java_installations, select_java
from miyu_launcher.core.paths import get_launcher_paths
from miyu_launcher.core.system import get_system_info


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Miyu Launcher")
        self.resize(1000, 600)

        system_info = get_system_info()
        launcher_paths = get_launcher_paths()
        launcher_paths.create()

        java_installations = find_java_installations()
        selected_java = select_java()

        title = QLabel("Miyu Launcher")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: 600;")

        subtitle = QLabel("Fase 1 — Core mínimo")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ram = (
            f"{system_info.total_ram_gb} GB"
            if system_info.total_ram_gb is not None
            else "No disponible"
        )

        system_label = QLabel(
            f"Sistema: {system_info.operating_system} {system_info.release}\n"
            f"Arquitectura: {system_info.architecture}\n"
            f"RAM detectada: {ram}\n"
            f"Datos del launcher: {launcher_paths.root}"
        )
        system_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if selected_java is not None:
            java_version = selected_java.version or "desconocida"
            java_major = selected_java.major if selected_java.major is not None else "?"
            java_text = (
                f"Java seleccionado: {java_version} (major {java_major})\n"
                f"Ruta: {selected_java.executable}\n"
                f"Instalaciones detectadas: {len(java_installations)}"
            )
        else:
            java_text = "Java seleccionado: no encontrado\nInstalaciones detectadas: 0"

        java_label = QLabel(java_text)
        java_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        java_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        play_button = QPushButton("JUGAR")
        play_button.setEnabled(False)
        play_button.setToolTip("Se habilitará cuando implementemos el lanzamiento de Minecraft.")
        play_button.setFixedWidth(220)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(system_label)
        layout.addSpacing(18)
        layout.addWidget(java_label)
        layout.addSpacing(24)
        layout.addWidget(play_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
