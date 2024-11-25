import sys
import json
import sqlite3
import os
import shutil
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QFileDialog,
    QGroupBox, QGridLayout, QFormLayout, QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene, QScrollArea, QGraphicsPixmapItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

# Настройка логгера
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class CreateEditModuleWindow(QMainWindow):
    update_signal = pyqtSignal()

    def __init__(self, module_id=None, parent=None):
        super().__init__()
        self.setWindowTitle("Create/Edit Module")
        self.setGeometry(100, 100, 800, 600)

        self.temp_terms = []  # Временный список для хранения терминов
        self.current_term_id = None  # ID текущего выбранного термина
        self.module_id = module_id
        self.parent = parent
        self.module_saved = False  # Флаг, указывающий, что модуль был успешно сохранен

        self.init_ui()
        self.init_db()

        if self.module_id:
            self.load_module_data()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Module Info Group
        module_info_group = QGroupBox("Module Information")
        module_info_layout = QFormLayout()

        self.module_name_input = QLineEdit()
        self.module_description_input = QTextEdit()
        self.module_theme_input = QLineEdit()

        module_info_layout.addRow(QLabel("Module Name:"), self.module_name_input)
        module_info_layout.addRow(QLabel("Module Description:"), self.module_description_input)
        module_info_layout.addRow(QLabel("Module Theme:"), self.module_theme_input)

        module_info_group.setLayout(module_info_layout)
        self.layout.addWidget(module_info_group)

        # Term and Definition Group
        term_def_group = QGroupBox("Term and Definition")
        term_def_layout = QGridLayout()

        self.term_input = QLineEdit()
        self.definition_input = QTextEdit()
        self.complexity_combo = QComboBox()
        self.complexity_combo.addItems(["Easy", "Normal", "Hard"])
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Image path")
        self.upload_image_button = QPushButton("Upload Image")
        self.upload_image_button.clicked.connect(self.upload_image)
        self.view_image_button = QPushButton("View Image")
        self.view_image_button.clicked.connect(self.view_image)

        term_def_layout.addWidget(QLabel("Term:"), 0, 0)
        term_def_layout.addWidget(self.term_input, 0, 1)
        term_def_layout.addWidget(QLabel("Definition:"), 1, 0)
        term_def_layout.addWidget(self.definition_input, 1, 1)
        term_def_layout.addWidget(QLabel("Complexity:"), 2, 0)
        term_def_layout.addWidget(self.complexity_combo, 2, 1)
        term_def_layout.addWidget(QLabel("Image Path:"), 3, 0)
        term_def_layout.addWidget(self.image_path_input, 3, 1)
        term_def_layout.addWidget(self.upload_image_button, 3, 2)
        term_def_layout.addWidget(self.view_image_button, 4, 1)

        term_def_group.setLayout(term_def_layout)
        self.layout.addWidget(term_def_group)

        # Import Data Group
        import_group = QGroupBox("Import Data")
        import_layout = QVBoxLayout()

        self.import_button = QPushButton("Import Data")
        self.import_button.clicked.connect(self.import_data)
        self.import_text_field = QTextEdit()
        self.import_text_field.setPlaceholderText("Term 1\tDefinition 1\nTerm 2\tDefinition 2\nTerm 3\tDefinition 3")

        import_layout.addWidget(self.import_button)
        import_layout.addWidget(self.import_text_field)

        import_group.setLayout(import_layout)
        self.layout.addWidget(import_group)

        # Separators Group
        separators_group = QGroupBox("Separators")
        separators_layout = QGridLayout()

        self.separator_combo = QComboBox()
        self.separator_combo.addItems(["Tab", "Comma", "Semicolon", "Line Break"])
        self.custom_separator_input = QLineEdit()
        self.custom_separator_input.setPlaceholderText("Custom separator")

        self.card_separator_combo = QComboBox()
        self.card_separator_combo.addItems(["Line Break", "Semicolon", "Comma", "Tab"])
        self.custom_card_separator_input = QLineEdit()
        self.custom_card_separator_input.setPlaceholderText("Custom separator")

        separators_layout.addWidget(QLabel("Between the term and the definition:"), 0, 0)
        separators_layout.addWidget(self.separator_combo, 0, 1)
        separators_layout.addWidget(self.custom_separator_input, 0, 2)
        separators_layout.addWidget(QLabel("Between the cards:"), 1, 0)
        separators_layout.addWidget(self.card_separator_combo, 1, 1)
        separators_layout.addWidget(self.custom_card_separator_input, 1, 2)

        separators_group.setLayout(separators_layout)
        self.layout.addWidget(separators_group)

        # Buttons Group
        buttons_group = QGroupBox("Actions")
        buttons_layout = QHBoxLayout()

        self.add_term_button = QPushButton("Add Term")
        self.add_term_button.clicked.connect(self.add_term)
        self.edit_term_button = QPushButton("Edit Term")
        self.edit_term_button.clicked.connect(self.edit_selected_term)
        self.delete_term_button = QPushButton("Delete Term")
        self.delete_term_button.clicked.connect(self.delete_selected_term)
        self.import_terms_button = QPushButton("Import Terms")
        self.import_terms_button.clicked.connect(self.import_terms)
        self.save_button = QPushButton("Save Module")
        self.save_button.clicked.connect(self.save_module)

        buttons_layout.addWidget(self.add_term_button)
        buttons_layout.addWidget(self.edit_term_button)
        buttons_layout.addWidget(self.delete_term_button)
        buttons_layout.addWidget(self.import_terms_button)
        buttons_layout.addWidget(self.save_button)

        buttons_group.setLayout(buttons_layout)
        self.layout.addWidget(buttons_group)

        # List of Terms
        self.term_list = QListWidget()
        self.term_list.itemClicked.connect(self.edit_term)
        self.layout.addWidget(self.term_list)

    def init_db(self):
        self.conn = sqlite3.connect('vocabify.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                definition TEXT NOT NULL,
                complexity TEXT DEFAULT 'Normal',
                image_path TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                theme TEXT,
                length INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def load_module_data(self):
        try:
            with open('modules.json', 'r') as f:
                modules_json = json.load(f)
        except (FileNotFoundError, ValueError):
            modules_json = {}

        if str(self.module_id) in modules_json:
            module_data = modules_json[str(self.module_id)]
            self.module_name_input.setText(module_data['name'])
            self.module_description_input.setText(module_data['description'])

            self.temp_terms = []
            for term_id in module_data['term_ids']:
                self.cursor.execute('SELECT term, definition, complexity, image_path FROM terms WHERE id = ?',
                                    (term_id,))
                term_data = self.cursor.fetchone()
                if term_data:
                    self.temp_terms.append({
                        "term": term_data[0],
                        "definition": term_data[1],
                        "complexity": term_data[2],
                        "image_path": term_data[3]
                    })
            self.update_term_list()

    def add_term(self):
        term = self.term_input.text()
        definition = self.definition_input.toPlainText()  # Используем toPlainText() для сохранения обычного текста
        complexity = self.complexity_combo.currentText()
        image_path = self.image_path_input.text()

        if term and definition:
            self.temp_terms.append({
                "term": term,
                "definition": definition,
                "complexity": complexity,
                "image_path": image_path
            })

            self.term_input.clear()
            self.definition_input.clear()
            self.image_path_input.clear()
            self.update_term_list()

    def update_term_list(self):
        self.term_list.clear()
        for term in self.temp_terms:
            item = QListWidgetItem(f"{term['term']}: {term['definition']}")
            self.term_list.addItem(item)

    def edit_term(self, item):
        term_text = item.text()
        term = term_text.split(":")[0].strip()
        definition = term_text.split(":")[1].strip()

        for i, term_data in enumerate(self.temp_terms):
            if term_data['term'] == term and term_data['definition'] == definition:
                self.term_input.setText(term_data['term'])
                self.definition_input.setText(term_data['definition'])  # Используем setText() для загрузки обычного текста
                self.complexity_combo.setCurrentText(term_data['complexity'])
                self.image_path_input.setText(term_data['image_path'])
                self.current_term_id = i
                break

    def edit_selected_term(self):
        if self.current_term_id is None:
            QMessageBox.warning(self, "Error", "No term selected.")
            return

        term = self.term_input.text()
        definition = self.definition_input.toPlainText()
        complexity = self.complexity_combo.currentText()
        image_path = self.image_path_input.text()

        if term and definition:
            self.temp_terms[self.current_term_id] = {
                "term": term,
                "definition": definition,
                "complexity": complexity,
                "image_path": image_path
            }

            self.term_input.clear()
            self.definition_input.clear()
            self.image_path_input.clear()
            self.update_term_list()

    def delete_selected_term(self):
        if self.current_term_id is None:
            QMessageBox.warning(self, "Error", "No term selected.")
            return

        # Удаляем термин из временного списка
        term_to_delete = self.temp_terms[self.current_term_id]
        del self.temp_terms[self.current_term_id]
        self.update_term_list()

        # Обновляем terms.json
        self.ensure_json_file_exists('terms.json')
        with open('terms.json', 'r') as f:
            terms = json.load(f)

        # Находим ID термина в базе данных
        self.cursor.execute('SELECT id FROM terms WHERE term = ? AND definition = ?',
                            (term_to_delete['term'], term_to_delete['definition']))
        term_id = self.cursor.fetchone()
        if term_id:
            term_id = term_id[0]
            if str(term_id) in terms:
                if self.module_id in terms[str(term_id)]['module_ids']:
                    terms[str(term_id)]['module_ids'].remove(self.module_id)
                    if not terms[str(term_id)]['module_ids']:
                        del terms[str(term_id)]

            with open('terms.json', 'w') as f:
                json.dump(terms, f, indent=4)

    def save_module(self):
        module_name = self.module_name_input.text()
        module_description = self.module_description_input.toPlainText()
        module_theme = self.module_theme_input.text()
        if not module_name:
            QMessageBox.warning(self, "Error", "Module name is required.")
            return

        if not self.temp_terms:
            QMessageBox.warning(self, "Error", "At least one term is required to save the module.")
            return

        # Сохраняем термины в terms.db
        term_ids = []
        try:
            with self.conn:
                for term in self.temp_terms:
                    # Вставляем термин в базу данных и получаем его ID
                    self.cursor.execute('''
                        INSERT INTO terms (term, definition, complexity, image_path)
                        VALUES (?, ?, ?, ?)
                    ''', (term['term'], term['definition'], term['complexity'], term['image_path']))
                    term_id = self.cursor.lastrowid
                    term_ids.append(term_id)

                    # Копируем изображение в папку проекта, если оно есть
                    if term['image_path']:
                        term['image_path'] = self.copy_image_to_project_folder(term['image_path'], term_id)

                    # Обновляем путь к изображению в базе данных
                    self.cursor.execute('''
                        UPDATE terms
                        SET image_path = ?
                        WHERE id = ?
                    ''', (term['image_path'], term_id))
        except sqlite3.Error as e:
            logging.error(f"Error saving terms to database: {e}")
            QMessageBox.critical(self, "Database Error", f"Error saving terms to database: {e}")
            return

        # Сохраняем модуль в modules.db
        try:
            with self.conn:
                if self.module_id:
                    self.cursor.execute('''
                        UPDATE modules
                        SET name = ?, theme = ?, length = ?
                        WHERE id = ?
                    ''', (module_name, module_theme, len(term_ids), self.module_id))
                else:
                    self.cursor.execute('''
                        INSERT INTO modules (name, theme, length)
                        VALUES (?, ?, ?)
                    ''', (module_name, module_theme, len(term_ids)))
                    self.module_id = self.cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Error saving module to database: {e}")
            QMessageBox.critical(self, "Database Error", f"Error saving module to database: {e}")
            return

        # Сохраняем модуль в modules.json
        module_data = {
            "id": self.module_id,
            "name": module_name,
            "description": module_description,
            "term_ids": term_ids,
            "theme": module_theme
        }
        try:
            self.save_module_to_json(module_data)
        except Exception as e:
            logging.error(f"Error saving module to JSON: {e}")
            QMessageBox.critical(self, "JSON Error", f"Error saving module to JSON: {e}")
            return

        # Сохраняем термины в terms.json
        try:
            self.save_terms_to_json(term_ids)
        except Exception as e:
            logging.error(f"Error saving terms to JSON: {e}")
            QMessageBox.critical(self, "JSON Error", f"Error saving terms to JSON: {e}")
            return

        QMessageBox.information(self, "Success", "Module saved successfully.")
        self.module_saved = True  # Устанавливаем флаг, что модуль был успешно сохранен
        self.update_signal.emit()
        self.close()

    def save_module_to_json(self, module_data):
        self.ensure_json_file_exists('modules.json')
        try:
            with open('modules.json', 'r') as f:
                modules = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error loading modules JSON: {e}")
            modules = {}

        modules[module_data['id']] = module_data

        try:
            with open('modules.json', 'w') as f:
                json.dump(modules, f, indent=4)
        except IOError as e:
            logging.error(f"Error writing modules JSON: {e}")
            raise

    def save_terms_to_json(self, term_ids):
        self.ensure_json_file_exists('terms.json')
        try:
            with open('terms.json', 'r') as f:
                terms = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error loading terms JSON: {e}")
            terms = {}

        for term_id in term_ids:
            if str(term_id) in terms:
                if self.module_id not in terms[str(term_id)]['module_ids']:
                    terms[str(term_id)]['module_ids'].append(self.module_id)
            else:
                terms[str(term_id)] = {
                    "module_ids": [self.module_id],
                    "image_path": self.temp_terms[term_ids.index(term_id)]['image_path']
                }

        try:
            with open('terms.json', 'w') as f:
                json.dump(terms, f, indent=4)
        except IOError as e:
            logging.error(f"Error writing terms JSON: {e}")
            raise

    def closeEvent(self, event):
        if self.module_saved:
            event.accept()
        else:
            reply = QMessageBox.question(self, 'Confirmation', 'Are you sure you want to close the window?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.update_signal.emit()
                event.accept()
            else:
                event.ignore()

    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = file.read()
                    self.import_text_field.setText(data)
            except IOError as e:
                logging.error(f"Error reading file: {e}")
                QMessageBox.critical(self, "File Error", f"Error reading file: {e}")

    def import_terms(self):
        data = self.import_text_field.toPlainText()  # Используем toPlainText() для получения текста без форматирования
        term_separator = self.get_separator(self.separator_combo, self.custom_separator_input)
        card_separator = self.get_separator(self.card_separator_combo, self.custom_card_separator_input)

        terms = []
        errors = []
        for card in data.split(card_separator):
            card = card.strip()
            if card:
                try:
                    term, definition = card.split(term_separator, 1)
                    term = term.strip()
                    definition = definition.strip()
                    if term and definition:
                        terms.append({
                            "term": term,
                            "definition": definition,
                            "complexity": "Normal",
                            "image_path": ""
                        })
                    else:
                        errors.append(card)
                except ValueError:
                    errors.append(card)

        self.temp_terms.extend(terms)
        self.update_term_list()

        if errors:
            self.import_text_field.setText("\n".join(errors))
            QMessageBox.warning(self, "Import Errors",
                                "Some lines could not be imported. Check the text field for details.")

    def get_separator(self, combo, custom_input):
        selected_separator = combo.currentText()
        if custom_input.text():
            return custom_input.text()
        if selected_separator == "Tab":
            return "\t"
        elif selected_separator == "Line Break":
            return "\n"
        elif selected_separator == "Comma":
            return ","
        elif selected_separator == "Semicolon":
            return ";"

    def ensure_json_file_exists(self, filename):
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump({}, f)

    def ensure_images_folder_exists(self):
        if not os.path.exists('images'):
            os.makedirs('images')

    def copy_image_to_project_folder(self, source_path, term):
        self.ensure_images_folder_exists()
        filename = os.path.basename(source_path)
        file_extension = os.path.splitext(filename)[1]
        destination_path = os.path.join('images', f"{term}{file_extension}")
        shutil.copy(source_path, destination_path)
        return destination_path

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "",
                                                   "Images (*.png *.xpm *.jpg *.bmp);;All Files (*)")
        if file_path:
            self.image_path_input.setText(file_path)

    def view_image(self):
        image_path = self.image_path_input.text()
        if image_path:
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