import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QSpinBox,
                             QTextEdit)
from db_connection import get_connection
from report_functions import save_report


class DriversWindow(QWidget):
    def __init__(self, role="employee"):
        super().__init__()
        self.role = role
        self.setWindowTitle(f"Управление водителями ({role})")
        self.resize(900, 550)
        self.selected_id = None
        self.init_ui()
        self.load_data()
        self.apply_role_restrictions()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Фамилия", "Имя", "Отчество",
                                              "Телефон", "Стаж", "Категория"])
        self.table.cellClicked.connect(self.select_row)
        main_layout.addWidget(self.table)

        form_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Фамилия:"))
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Введите фамилию")
        row1.addWidget(self.last_name_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Имя:"))
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Введите имя")
        row2.addWidget(self.first_name_input)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Отчество:"))
        self.patronymic_input = QLineEdit()
        self.patronymic_input.setPlaceholderText("Введите отчество (необязательно)")
        row3.addWidget(self.patronymic_input)
        form_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Телефон:"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7(XXX)XXX-XX-XX")
        row4.addWidget(self.phone_input)
        form_layout.addLayout(row4)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Стаж (лет):"))
        self.experience_input = QSpinBox()
        self.experience_input.setMinimum(0)
        self.experience_input.setMaximum(60)
        self.experience_input.setValue(0)
        row5.addWidget(self.experience_input)
        form_layout.addLayout(row5)

        row6 = QHBoxLayout()
        row6.addWidget(QLabel("Категория:"))
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("B, C, D, E")
        row6.addWidget(self.category_input)
        form_layout.addLayout(row6)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_driver)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_driver)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_driver)
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
            cursor.execute("""SELECT id_driver, last_name, first_name, patronymic,
                              phone_number, experience, category
                              FROM Drivers ORDER BY id_driver;""")
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
            self.last_name_input.setText(self.table.item(row, 1).text())
            self.first_name_input.setText(self.table.item(row, 2).text())
            self.patronymic_input.setText(self.table.item(row, 3).text())
            self.phone_input.setText(self.table.item(row, 4).text())
            self.experience_input.setValue(int(self.table.item(row, 5).text()))
            self.category_input.setText(self.table.item(row, 6).text())
        except Exception:
            pass

    def add_driver(self):
        last_name = self.last_name_input.text().strip()
        first_name = self.first_name_input.text().strip()
        patronymic = self.patronymic_input.text().strip()
        phone = self.phone_input.text().strip()
        experience = self.experience_input.value()
        category = self.category_input.text().strip()

        if not last_name or not first_name:
            QMessageBox.warning(self, "Ошибка", "Введите фамилию и имя!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO Drivers (last_name, first_name, patronymic,
                           phone_number, med_indications, experience, category)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                           (last_name, first_name, patronymic, phone,
                            "Нет", experience, category))
            conn.commit()
            QMessageBox.information(self, "Успех", "Водитель добавлен!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_driver(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите водителя!")
            return

        last_name = self.last_name_input.text().strip()
        first_name = self.first_name_input.text().strip()
        patronymic = self.patronymic_input.text().strip()
        phone = self.phone_input.text().strip()
        experience = self.experience_input.value()
        category = self.category_input.text().strip()

        if not last_name or not first_name:
            QMessageBox.warning(self, "Ошибка", "Введите фамилию и имя!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""UPDATE Drivers SET last_name = %s, first_name = %s,
                           patronymic = %s, phone_number = %s, experience = %s,
                           category = %s WHERE id_driver = %s""",
                           (last_name, first_name, patronymic, phone,
                            experience, category, self.selected_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Данные обновлены!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_driver(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите водителя!")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Удалить этого водителя?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Drivers WHERE id_driver = %s", (self.selected_id,))
            conn.commit()
            QMessageBox.information(self, "Успех", "Водитель удален!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def clear_inputs(self):
        self.selected_id = None
        self.last_name_input.clear()
        self.first_name_input.clear()
        self.patronymic_input.clear()
        self.phone_input.clear()
        self.experience_input.setValue(0)
        self.category_input.clear()

    def apply_role_restrictions(self):
        if self.role == "employee":
            self.add_btn.setEnabled(False)
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.last_name_input.setReadOnly(True)
            self.first_name_input.setReadOnly(True)
            self.patronymic_input.setReadOnly(True)
            self.phone_input.setReadOnly(True)
            self.experience_input.setEnabled(False)
            self.category_input.setReadOnly(True)

    def generate_report(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT id_driver, last_name, first_name, patronymic,
                              phone_number, experience, category
                              FROM Drivers ORDER BY experience DESC;""")
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 60 + "\n"
            report_text += "ОТЧЕТ ПО ВОДИТЕЛЯМ АВТОПАРКА\n"
            report_text += "=" * 60 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего водителей: {len(rows)}\n\n"

            total_experience = sum(row[5] for row in rows)
            avg_experience = total_experience / len(rows) if rows else 0
            report_text += f"Средний стаж водителей: {avg_experience:.1f} лет\n"
            report_text += "=" * 60 + "\n\n"

            for row in rows:
                id_driver, last_name, first_name, patronymic, phone, exp, category = row
                full_name = f"{last_name} {first_name} {patronymic}".strip()
                report_text += f"ID: {id_driver} | {full_name}\n"
                report_text += f"Телефон: {phone} | Стаж: {exp} лет\n"
                report_text += f"Категория: {category}\n"
                report_text += "-" * 40 + "\n"

            success, message = save_report(report_text, "drivers_report")
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
        preview.setWindowTitle("Просмотр отчета - Водители")
        preview.resize(550, 450)

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