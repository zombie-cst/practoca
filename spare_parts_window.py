import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QSpinBox,
                             QTextEdit)
from db_connection import get_connection
from report_functions import save_report


class SparePartsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление запчастями")
        self.resize(800, 500)
        self.selected_id = None
        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Наименование", "Количество"])
        self.table.cellClicked.connect(self.select_row)
        main_layout.addWidget(self.table)

        form_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Наименование:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите название запчасти")
        row1.addWidget(self.name_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Количество:"))
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(0)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setValue(0)
        row2.addWidget(self.quantity_input)
        form_layout.addLayout(row2)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_part)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_part)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_part)
        btn_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)

        self.report_btn = QPushButton("Создать отчет")
        self.report_btn.clicked.connect(self.generate_report)
        btn_layout.addWidget(self.report_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_data(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id_spare_part, type_sp, quantity FROM SpareParts ORDER BY id_spare_part;")
            rows = cursor.fetchall()
            self.table.setRowCount(0)
            for row_idx, row_data in enumerate(rows):
                self.table.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            self.table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def select_row(self, row, column):
        try:
            self.selected_id = self.table.item(row, 0).text()
            self.name_input.setText(self.table.item(row, 1).text())
            self.quantity_input.setValue(int(self.table.item(row, 2).text()))
        except Exception:
            pass

    def add_part(self):
        name = self.name_input.text().strip()
        quantity = self.quantity_input.value()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите наименование!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO SpareParts (type_sp, quantity) VALUES (%s, %s)",
                           (name, quantity))
            conn.commit()
            QMessageBox.information(self, "Успех", "Запчасть добавлена!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_part(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запчасть!")
            return

        name = self.name_input.text().strip()
        quantity = self.quantity_input.value()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите наименование!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE SpareParts SET type_sp = %s, quantity = %s WHERE id_spare_part = %s",
                           (name, quantity, self.selected_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Данные обновлены!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_part(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запчасть!")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Удалить эту запчасть?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM SpareParts WHERE id_spare_part = %s", (self.selected_id,))
            conn.commit()
            QMessageBox.information(self, "Успех", "Запчасть удалена!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def clear_inputs(self):
        self.selected_id = None
        self.name_input.clear()
        self.quantity_input.setValue(0)

    def generate_report(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id_spare_part, type_sp, quantity FROM SpareParts ORDER BY type_sp;")
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 60 + "\n"
            report_text += "ОТЧЕТ ПО ЗАПАСНЫМ ЧАСТЯМ\n"
            report_text += "=" * 60 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего наименований: {len(rows)}\n\n"

            total_quantity = sum(row[2] for row in rows)
            report_text += f"Общее количество на складе: {total_quantity} шт.\n"
            report_text += "=" * 60 + "\n\n"

            for row in rows:
                id_part, name, quantity = row
                report_text += f"ID: {id_part} | {name}\n"
                report_text += f"Количество: {quantity} шт.\n"
                report_text += "-" * 40 + "\n"

            success, message = save_report(report_text, "spare_parts_report")
            if success:
                QMessageBox.information(self, "Успех", message)
                self.show_report_preview(report_text)
            else:
                QMessageBox.critical(self, "Ошибка", message)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании отчета: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def show_report_preview(self, report_text):
        preview = QWidget()
        preview.setWindowTitle("Просмотр отчета - Запчасти")
        preview.resize(500, 400)

        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(report_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(preview.close)
        layout.addWidget(close_btn)
        preview.setLayout(layout)
        preview.show()