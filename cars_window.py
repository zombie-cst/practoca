import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QSpinBox,
                             QComboBox, QTextEdit)
from db_connection import get_connection
from report_functions import save_report


class CarsWindow(QWidget):
    def __init__(self, role="employee"):
        super().__init__()
        self.role = role
        self.setWindowTitle(f"Управление автомобилями ({role})")
        self.resize(900, 500)
        self.selected_id = None
        self.init_ui()
        self.load_data()
        self.apply_role_restrictions()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Марка", "Модель",
                                              "Год выпуска", "Пробег", "Статус"])
        self.table.cellClicked.connect(self.select_row)
        main_layout.addWidget(self.table)

        form_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Марка:"))
        self.brand_input = QLineEdit()
        row1.addWidget(self.brand_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Модель:"))
        self.model_input = QLineEdit()
        row2.addWidget(self.model_input)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Год выпуска:"))
        self.year_input = QSpinBox()
        self.year_input.setMinimum(1990)
        self.year_input.setMaximum(datetime.now().year + 1)
        self.year_input.setValue(2020)
        row3.addWidget(self.year_input)
        form_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Пробег:"))
        self.mileage_input = QSpinBox()
        self.mileage_input.setMinimum(0)
        self.mileage_input.setMaximum(9999999)
        self.mileage_input.setValue(0)
        row4.addWidget(self.mileage_input)
        form_layout.addLayout(row4)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Статус:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Свободен", "Рейс", "Техобслуживание"])
        row5.addWidget(self.status_combo)
        form_layout.addLayout(row5)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_car)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_car)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_car)
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
            cursor.execute("""SELECT id_car, brand, model, year_release,
                              car_mileage, status FROM Cars ORDER BY id_car;""")
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
            self.brand_input.setText(self.table.item(row, 1).text())
            self.model_input.setText(self.table.item(row, 2).text())
            self.year_input.setValue(int(self.table.item(row, 3).text()))
            self.mileage_input.setValue(int(self.table.item(row, 4).text()))
            status = self.table.item(row, 5).text()
            index = self.status_combo.findText(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
        except Exception as e:
            pass

    def add_car(self):
        brand = self.brand_input.text().strip()
        model = self.model_input.text().strip()
        year = self.year_input.value()
        mileage = self.mileage_input.value()
        status = self.status_combo.currentText()

        if not brand or not model:
            QMessageBox.warning(self, "Ошибка", "Введите марку и модель!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO Cars (brand, model, year_release,
                           car_mileage, status) VALUES (%s, %s, %s, %s, %s)""",
                           (brand, model, year, mileage, status))
            conn.commit()
            QMessageBox.information(self, "Успех", "Автомобиль добавлен!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_car(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return

        brand = self.brand_input.text().strip()
        model = self.model_input.text().strip()
        year = self.year_input.value()
        mileage = self.mileage_input.value()
        status = self.status_combo.currentText()

        if not brand or not model:
            QMessageBox.warning(self, "Ошибка", "Введите марку и модель!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""UPDATE Cars SET brand = %s, model = %s, year_release = %s,
                           car_mileage = %s, status = %s WHERE id_car = %s""",
                           (brand, model, year, mileage, status, self.selected_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Данные обновлены!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_car(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Удалить этот автомобиль?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Cars WHERE id_car = %s", (self.selected_id,))
            conn.commit()
            QMessageBox.information(self, "Успех", "Автомобиль удален!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def clear_inputs(self):
        self.selected_id = None
        self.brand_input.clear()
        self.model_input.clear()
        self.year_input.setValue(2020)
        self.mileage_input.setValue(0)
        self.status_combo.setCurrentIndex(0)

    def apply_role_restrictions(self):
        if self.role == "employee":
            self.add_btn.setEnabled(False)
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.brand_input.setReadOnly(True)
            self.model_input.setReadOnly(True)
            self.year_input.setEnabled(False)
            self.mileage_input.setEnabled(False)
            self.status_combo.setEnabled(False)

    def generate_report(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT id_car, brand, model, year_release,
                              car_mileage, status FROM Cars ORDER BY brand;""")
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 60 + "\n"
            report_text += "ОТЧЕТ ПО АВТОМОБИЛЯМ АВТОПАРКА\n"
            report_text += "=" * 60 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего автомобилей: {len(rows)}\n\n"

            status_counts = {}
            for row in rows:
                status = row[5]
                status_counts[status] = status_counts.get(status, 0) + 1

            report_text += "Статистика по статусам:\n"
            for status, count in status_counts.items():
                status_rus = {"active": "В работе", "maintenance": "На ТО",
                              "repair": "В ремонте", "decommissioned": "Списан"}
                report_text += f"  {status_rus.get(status, status)}: {count} шт.\n"
            report_text += "=" * 60 + "\n\n"

            for row in rows:
                id_car, brand, model, year, mileage, status = row
                status_rus = {"active": "В работе", "maintenance": "На ТО",
                              "repair": "В ремонте", "decommissioned": "Списан"}
                report_text += f"ID: {id_car} | {brand} {model}\n"
                report_text += f"Год выпуска: {year} | Пробег: {mileage} км\n"
                report_text += f"Статус: {status_rus.get(status, status)}\n"
                report_text += "-" * 40 + "\n"

            success, message = save_report(report_text, "cars_report")
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
        preview.setWindowTitle("Просмотр отчета - Автомобили")
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