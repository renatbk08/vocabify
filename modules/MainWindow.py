import json
import sqlite3
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QGridLayout, QLineEdit, QMessageBox, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush, QIcon
from application.modules.CreateEditModuleWindow import CreateEditModuleWindow
from application.modules.MemorizationWindow import MemorizationWindow  # Импортируем MemorizationWindow

class ModuleWidget(QWidget):
    def __init__(self, name, term_count, description, module_id, parent):
        super().__init__()
        self.module_id = module_id
        self.parent = parent
        self.setUI(name, term_count, description)

    def setUI(self, name, term_count, description):
        layout = QGridLayout()

        # Название модуля
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(name_label, 0, 0, 1, 2)

        # Количество терминов
        term_count_label = QLabel(f"Terms: {term_count}")
        term_count_label.setFont(QFont("Arial", 12))
        term_count_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(term_count_label, 1, 0, 1, 2)

        # Описание
        description_label = QLabel(description)
        description_label.setFont(QFont("Arial", 12))
        description_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        description_label.setWordWrap(True)
        layout.addWidget(description_label, 2, 0, 1, 2)

        # Кнопки редактирования, удаления и изучения
        button_layout = QHBoxLayout()

        edit_button = QPushButton("Edit")
        edit_button.setFont(QFont("Arial", 12))
        edit_button.setFixedSize(80, 30)
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        edit_button.clicked.connect(self.edit_module)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete")
        delete_button.setFont(QFont("Arial", 12))
        delete_button.setFixedSize(80, 30)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        delete_button.clicked.connect(self.delete_module)
        button_layout.addWidget(delete_button)

        study_button = QPushButton("Study")
        study_button.setFont(QFont("Arial", 12))
        study_button.setFixedSize(80, 30)
        study_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        study_button.clicked.connect(self.study_module)
        button_layout.addWidget(study_button)

        layout.addLayout(button_layout, 3, 1, 1, 1, Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

        # Установка фонового градиента
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#f0f0f0"))
        gradient.setColorAt(1, QColor("#e0e0e0"))
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)

        # Установка минимального размера виджета
        self.setMinimumSize(300, 150)

    def edit_module(self):
        self.parent.open_edit_window(self.module_id)

    def delete_module(self):
        reply = QMessageBox.question(self, 'Confirm Deletion', 'Are you sure you want to delete this module?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.parent.delete_module(self.module_id)

    def study_module(self):
        self.parent.open_study_window(self.module_id)


class MainWindow(QMainWindow):
    update_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setUI()
        self.modules = self.load_modules()
        self.current_page = 0
        self.modules_per_page = 6
        self.init_modules()

        self.update_signal.connect(self.update_modules)

    def setUI(self):
        self.setWindowTitle("Vocabify")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('icon.ico'))
        # Основной виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Основной layout
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Верхний layout
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.setAlignment(top_layout, Qt.AlignmentFlag.AlignTop)

        # Кнопка настроек
        settings_button = QPushButton("Settings")
        settings_button.setFixedSize(90, 30)
        top_layout.addWidget(settings_button)
        top_layout.setAlignment(settings_button, Qt.AlignmentFlag.AlignLeft)

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setFixedSize(200, 30)
        self.search_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.search_input.returnPressed.connect(self.search)
        top_layout.addWidget(self.search_input)
        top_layout.setAlignment(self.search_input, Qt.AlignmentFlag.AlignRight)

        # Центральный layout
        content_layout = QVBoxLayout()
        main_layout.addLayout(content_layout)
        main_layout.setAlignment(content_layout, Qt.AlignmentFlag.AlignTop)

        # Кнопка добавления нового модуля
        add_button = QPushButton("+")
        add_button.setFixedSize(30, 30)
        add_button.clicked.connect(self.open_create_window)
        top_content_layout = QHBoxLayout()
        top_content_layout.addWidget(add_button)
        top_content_layout.setAlignment(add_button, Qt.AlignmentFlag.AlignRight)
        content_layout.addLayout(top_content_layout)

        content_layout_horizontal = QHBoxLayout()
        # Кнопка "назад"
        self.back_button = QPushButton("<")
        self.back_button.setFixedSize(30, 30)
        self.back_button.clicked.connect(self.previous_page)
        content_layout_horizontal.addWidget(self.back_button)

        # Сетка модулей
        self.module_grid = QGridLayout()
        content_layout_horizontal.addLayout(self.module_grid)

        # Кнопка "вперед"
        self.forward_button = QPushButton(">")
        self.forward_button.setFixedSize(30, 30)
        self.forward_button.clicked.connect(self.next_page)
        content_layout_horizontal.addWidget(self.forward_button)
        content_layout.addLayout(content_layout_horizontal)

    def load_modules(self):
        try:
            conn = sqlite3.connect('vocabify.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, theme, length FROM modules')
            modules_db = cursor.fetchall()
            conn.close()
        except sqlite3.OperationalError:
            modules_db = []

        try:
            with open('modules.json', 'r') as f:
                modules_json = json.load(f)
        except (FileNotFoundError, ValueError):
            modules_json = {}

        modules = []
        for module in modules_db:
            module_id, name, theme, length = module
            if str(module_id) in modules_json:
                description = modules_json[str(module_id)]['description']
                modules.append({
                    'id': module_id,
                    'name': name,
                    'theme': theme,
                    'length': length,
                    'description': description
                })
        return modules

    def init_modules(self):
        self.module_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.update_modules_grid()

    def update_modules(self):
        self.modules = self.load_modules()
        self.update_modules_grid()

    def update_modules_grid(self):
        for i in reversed(range(self.module_grid.count())):
            self.module_grid.itemAt(i).widget().setParent(None)

        if not self.modules:
            no_modules_label = QLabel("No modules available.")
            no_modules_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.module_grid.addWidget(no_modules_label, 0, 0)
            return

        start = self.current_page * self.modules_per_page
        end = start + self.modules_per_page
        for i, module in enumerate(self.modules[start:end]):
            module_widget = ModuleWidget(module['name'], module['length'], module['description'], module['id'], self)
            self.module_grid.addWidget(module_widget, i // 3, i % 3)

        self.back_button.setEnabled(self.current_page > 0)
        self.forward_button.setEnabled(end < len(self.modules))

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_modules_grid()

    def next_page(self):
        if (self.current_page + 1) * self.modules_per_page < len(self.modules):
            self.current_page += 1
            self.update_modules_grid()

    def open_create_window(self):
        self.create_edit_window = CreateEditModuleWindow(parent=self)
        self.create_edit_window.update_signal.connect(self.update_modules)  # Подключаем сигнал
        self.create_edit_window.show()

    def open_edit_window(self, module_id):
        self.create_edit_window = CreateEditModuleWindow(module_id=module_id, parent=self)
        self.create_edit_window.update_signal.connect(self.update_modules)  # Подключаем сигнал
        self.create_edit_window.show()

    def delete_module(self, module_id):
        try:
            with open('modules.json', 'r') as f:
                modules_json = json.load(f)
        except (FileNotFoundError, ValueError):
            modules_json = {}

        if str(module_id) in modules_json:
            del modules_json[str(module_id)]

            with open('modules.json', 'w') as f:
                json.dump(modules_json, f, indent=4)

            self.modules = self.load_modules()
            self.update_modules_grid()

    def open_study_window(self, module_id):
        self.study_window = MemorizationWindow(module_id=module_id, parent=self)
        self.study_window.show()

    def search(self):
        query = self.search_input.text().strip().lower()
        if not query:
            return

        conn = sqlite3.connect('vocabify.db')
        cursor = conn.cursor()

        # Поиск модуля по названию
        cursor.execute('SELECT id, name, theme, length FROM modules WHERE LOWER(name) LIKE ?', ('%' + query + '%',))
        module_results = cursor.fetchall()

        # Поиск термина
        cursor.execute('SELECT id, term, definition FROM terms WHERE LOWER(term) LIKE ?', ('%' + query + '%',))
        term_results = cursor.fetchall()

        conn.close()

        if module_results:
            module_id = module_results[0][0]
            self.open_study_window(module_id)
        elif term_results:
            self.show_term_results(term_results)
        else:
            QMessageBox.information(self, "Search Result", "No results found.")

    def show_term_results(self, term_results):
        term_dialog = QDialog(self)
        term_dialog.setWindowTitle("Search Results")
        term_dialog.setGeometry(100, 100, 400, 300)

        term_layout = QVBoxLayout()
        term_dialog.setLayout(term_layout)

        term_list = QListWidget()
        term_layout.addWidget(term_list)

        for term in term_results:
            term_id, term_text, definition = term
            item = QListWidgetItem(f"{term_text}: {definition}")
            term_list.addItem(item)

        term_dialog.exec()
