from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
    QLineEdit, QTabWidget, QListWidget, QGroupBox, QCheckBox, 
    QProgressBar, QProgressDialog, QInputDialog, QMessageBox,
    QTextEdit, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QColor, QFont, QFontDatabase

# ===== IMPORTS DO SISTEMA =====
import os
import sys
import re
import subprocess
import zipfile
import shutil

class PythonVersionManager:
    """Gerenciador de versões Python instaladas e para download"""

    def __init__(self):
        self.installed_versions = []
        self.available_versions = []
        self.scan_installed_versions()

    def scan_installed_versions(self):
        """Detecta versões Python instaladas no sistema"""
        self.installed_versions = []

        # Locais comuns de instalação
        search_paths = []

        if platform.system() == "Windows":
            search_paths = [
                "C:\\Python*",
                "C:\\Program Files\\Python*",
                "C:\\Users\\*\\AppData\\Local\\Programs\\Python\\Python*"
            ]
        elif platform.system() == "Linux":
            search_paths = [
                "/usr/bin/python*",
                "/usr/local/bin/python*",
                "/opt/python*"
            ]
        elif platform.system() == "Darwin":  # macOS
            search_paths = [
                "/usr/local/bin/python*",
                "/opt/homebrew/bin/python*",
                "/Applications/Python*"
            ]

        # Busca por executáveis Python
        for path_pattern in search_paths:
            for python_path in glob.glob(
                    path_pattern):
                if os.path.isfile(python_path) and not python_path.endswith(
                        ('config', 'm')):
                    try:
                        result = subprocess.run(
                            [python_path, "--version"],
                            capture_output=True, text=True, timeout=2
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip()
                            self.installed_versions.append({
                                'path': python_path,
                                'version': version,
                                'type': 'system'
                            })
                    except:
                        pass

        # Remove duplicatas
        seen = set()
        unique_versions = []
        for v in self.installed_versions:
            key = v['path']
            if key not in seen:
                seen.add(key)
                unique_versions.append(
                    v)

        self.installed_versions = unique_versions

    def get_available_versions(self):
        """Obtém versões disponíveis para download"""
        # Esta é uma implementação simplificada
        # Em produção, você faria web scraping do site oficial
        # do Python
        self.available_versions = [
            {'version': 'Python 3.12.0',
             'url': 'https://www.python.org/downloads/release/python-3120/'},
            {'version': 'Python 3.11.6',
             'url': 'https://www.python.org/downloads/release/python-3116/'},
            {'version': 'Python 3.10.12',
             'url': 'https://www.python.org/downloads/release/python-31012/'},
            {'version': 'Python 3.9.18',
             'url': 'https://www.python.org/downloads/release/python-3918/'},
        ]
        return self.available_versions

    def set_as_default(self, python_path):
        """Define uma versão Python como padrão no IDE"""
        try:
            # Verifica se é válido
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return python_path
        except:
            pass
        return None
