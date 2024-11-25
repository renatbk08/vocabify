import sys
import sqlite3
import logging
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QMessageBox, QInputDialog, QFileDialog, QGroupBox, QGridLayout, QFormLayout, QDialog,
    QVBoxLayout, QGraphicsView, QGraphicsScene, QScrollArea, QGraphicsPixmapItem, QLineEdit, QRadioButton,
    QButtonGroup, QTextEdit, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QFont

# Настройка логгера
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class MemorizationWindow(QMainWindow):
    def __init__(self, module_id, parent=None):
        super().__init__()
        self.module_id = module_id
        self.parent = parent
        self.terms = self.load_terms()
        self.current_term_index = 0
        self.show_back = False  # Флаг для отображения обратной стороны карточки
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Memorization Mode")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Card content
        self.content_group = QGroupBox()
        self.content_layout = QVBoxLayout()
        self.content_group.setLayout(self.content_layout)

        self.term_label = QLabel()
        self.term_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.term_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.content_layout.addWidget(self.term_label)

        self.definition_label = QLabel()
        self.definition_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.definition_label.setFont(QFont("Arial", 14))
        self.content_layout.addWidget(self.definition_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.content_layout.addWidget(self.image_label)

        self.layout.addWidget(self.content_group)

        # Navigation buttons
        self.nav_group = QGroupBox()
        self.nav_layout = QHBoxLayout()
        self.nav_group.setLayout(self.nav_layout)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous_term)
        self.nav_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_term)
        self.nav_layout.addWidget(self.next_button)

        self.flip_button = QPushButton("Show Back")
        self.flip_button.clicked.connect(self.flip_card)
        self.nav_layout.addWidget(self.flip_button)

        self.layout.addWidget(self.nav_group)

        # Initialize with the first term
        self.show_term()

    def load_terms(self):
        try:
            with open('modules.json', 'r') as f:
                modules = json.load(f)
                term_ids = modules[str(self.module_id)]['term_ids']

            conn = sqlite3.connect('vocabify.db')
            cursor = conn.cursor()
            cursor.execute('SELECT term, definition, image_path FROM terms WHERE id IN ({})'.format(','.join('?' for _ in term_ids)), term_ids)
            terms = cursor.fetchall()
            conn.close()
            logging.info(f"Loaded {len(terms)} terms for module ID {self.module_id}")
            return terms
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logging.error(f"Error loading terms from database or JSON file: {e}")
            return []

    def show_term(self):
        term, definition, image_path = self.terms[self.current_term_index]
        if self.show_back:
            self.term_label.setText(term)
            self.definition_label.setText(definition)
            if image_path:
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.mousePressEvent = lambda event: self.view_image(image_path)
            else:
                self.image_label.clear()
        else:
            self.term_label.setText(term)
            self.definition_label.clear()
            self.image_label.clear()
        logging.info(f"Showing term: {term}")

    def set_cards_mode(self):
        self.content_group.setTitle("Cards Mode")
        self.show_term()
        logging.info("Switched to cards mode")

    def show_previous_term(self):
        if self.current_term_index > 0:
            self.current_term_index -= 1
            self.show_back = False  # Сбрасываем флаг при переходе к предыдущему термину
            self.show_term()
            logging.info(f"Showing previous term: {self.terms[self.current_term_index][0]}")

    def show_next_term(self):
        if self.current_term_index < len(self.terms) - 1:
            self.current_term_index += 1
            self.show_back = False  # Сбрасываем флаг при переходе к следующему термину
            self.show_term()
            logging.info(f"Showing next term: {self.terms[self.current_term_index][0]}")

    def flip_card(self):
        self.show_back = not self.show_back
        self.show_term()
        logging.info(f"Flipping card to {'back' if self.show_back else 'front'}")

    def view_image(self, image_path):
        image_dialog = QDialog(self)
        image_dialog.setWindowTitle("View Image")
        image_dialog.setGeometry(100, 100, 600, 400)

        image_layout = QVBoxLayout()
        image_view = QGraphicsView()
        image_scene = QGraphicsScene()
        pixmap = QPixmap(image_path)
        image_item = QGraphicsPixmapItem(pixmap)
        image_scene.addItem(image_item)
        image_view.setScene(image_scene)
        image_layout.addWidget(image_view)

        image_dialog.setLayout(image_layout)
        image_dialog.exec()
        logging.info(f"Viewing image: {image_path}")
