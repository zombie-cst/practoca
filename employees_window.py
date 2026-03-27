import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QComboBox,
                             QTextEdit, QDialog, QFormLayout, QDialogButtonBox)
from db_connection import get_connection
from report_functions import save_report


class EmployeesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление сотрудниками")
        self.resize(1000, 600)
        self.selected_id = None
        self.init_ui()
        self.load_data()
        self.load_positions()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Фамилия", "Имя", "Отчество",
                                              "Телефон", "Email", "Должность"])
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
        row5.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@mail.com (необязательно)")
        row5.addWidget(self.email_input)
        form_layout.addLayout(row5)

        row6 = QHBoxLayout()
        row6.addWidget(QLabel("Должность:"))
        self.position_combo = QComboBox()
        row6.addWidget(self.position_combo)
        form_layout.addLayout(row6)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_employee)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_employee)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_employee)
        btn_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)

        self.add_position_btn = QPushButton("Добавить должность")
        self.add_position_btn.clicked.connect(self.add_position)
        btn_layout.addWidget(self.add_position_btn)

        self.report_btn = QPushButton("Создать отчет")
        self.report_btn.clicked.connect(self.generate_report)
        btn_layout.addWidget(self.report_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_positions(self):
        """Загрузка должностей из таблицы Positions"""
        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id_position, appointment FROM Positions ORDER BY id_position")
            positions = cursor.fetchall()
            self.position_combo.clear()
            for pos in positions:
                self.position_combo.addItem(pos[1], pos[0])
            
            if self.position_combo.count() == 0:
                self.position_combo.addItem("Нет доступных должностей", None)
                self.position_combo.setEnabled(False)
                self.add_btn.setEnabled(False)
            else:
                self.position_combo.setEnabled(True)
                self.add_btn.setEnabled(True)
        except Exception as e:
            print(f"Ошибка загрузки должностей: {e}")
        finally:
            cursor.close()
            conn.close()

    def load_data(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT e.id_employee, e.last_name, e.first_name, e.patronymic,
                              e.phone_number, e.gmail, p.appointment
                              FROM Employees e
                              LEFT JOIN Positions p ON e.position_id = p.id_position
                              ORDER BY e.id_employee;""")
            rows = cursor.fetchall()
            self.table.setRowCount(0)
            for row_idx, row_data in enumerate(rows):
                self.table.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    display_value = str(value) if value is not None else ""
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))
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
            
            patronymic = self.table.item(row, 3).text()
            if patronymic and patronymic != "":
                self.patronymic_input.setText(patronymic)
            else:
                self.patronymic_input.clear()
            
            self.phone_input.setText(self.table.item(row, 4).text())
            
            email = self.table.item(row, 5).text()
            if email and email != "":
                self.email_input.setText(email)
            else:
                self.email_input.clear()
            
            position = self.table.item(row, 6).text()
            for i in range(self.position_combo.count()):
                if self.position_combo.itemText(i) == position:
                    self.position_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            print(f"Ошибка выбора строки: {e}")

    def add_employee(self):
        last_name = self.last_name_input.text().strip()
        first_name = self.first_name_input.text().strip()
        patronymic = self.patronymic_input.text().strip() if self.patronymic_input.text().strip() else None
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip() if self.email_input.text().strip() else None
        position_id = self.position_combo.currentData()

        if not last_name:
            QMessageBox.warning(self, "Ошибка", "Введите фамилию!")
            return
        if not first_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя!")
            return
        if not phone:
            QMessageBox.warning(self, "Ошибка", "Введите телефон!")
            return
        if not position_id:
            QMessageBox.warning(self, "Ошибка", "Выберите должность!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO Employees (last_name, first_name, patronymic,
                           phone_number, gmail, position_id)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                           (last_name, first_name, patronymic, phone, email, position_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Сотрудник добавлен!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_employee(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника!")
            return

        last_name = self.last_name_input.text().strip()
        first_name = self.first_name_input.text().strip()
        patronymic = self.patronymic_input.text().strip() if self.patronymic_input.text().strip() else None
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip() if self.email_input.text().strip() else None
        position_id = self.position_combo.currentData()

        if not last_name:
            QMessageBox.warning(self, "Ошибка", "Введите фамилию!")
            return
        if not first_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя!")
            return
        if not phone:
            QMessageBox.warning(self, "Ошибка", "Введите телефон!")
            return
        if not position_id:
            QMessageBox.warning(self, "Ошибка", "Выберите должность!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""UPDATE Employees SET last_name = %s, first_name = %s,
                           patronymic = %s, phone_number = %s, gmail = %s,
                           position_id = %s WHERE id_employee = %s""",
                           (last_name, first_name, patronymic, phone, email,
                            position_id, self.selected_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Данные обновлены!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_employee(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника!")
            return

        reply = QMessageBox.question(self, "Подтверждение", 
                                     "Удалить этого сотрудника?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Employees WHERE id_employee = %s", (self.selected_id,))
            conn.commit()
            QMessageBox.information(self, "Успех", "Сотрудник удален!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def add_position(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление должности")
        dialog.resize(350, 180)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        name_input = QLineEdit()
        name_input.setPlaceholderText("Например: Механик, Диспетчер")
        form_layout.addRow("Название должности:", name_input)
        
        access_input = QLineEdit()
        access_input.setPlaceholderText("Описание прав доступа (необязательно)")
        form_layout.addRow("Права доступа:", access_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            position_name = name_input.text().strip()
            access = access_input.text().strip() if access_input.text().strip() else None
            
            if not position_name:
                QMessageBox.warning(self, "Ошибка", "Введите название должности!")
                return
            
            conn = get_connection()
            if not conn:
                QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
                return
            
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO Positions (appointment, access_p) VALUES (%s, %s)",
                               (position_name, access))
                conn.commit()
                QMessageBox.information(self, "Успех", f"Должность '{position_name}' добавлена!")
                self.load_positions()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении должности: {str(e)}")
            finally:
                cursor.close()
                conn.close()

    def clear_inputs(self):
        self.selected_id = None
        self.last_name_input.clear()
        self.first_name_input.clear()
        self.patronymic_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        if self.position_combo.count() > 0 and self.position_combo.currentData() is not None:
            self.position_combo.setCurrentIndex(0)

    def generate_report(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT e.id_employee, e.last_name, e.first_name, e.patronymic,
                              e.phone_number, e.gmail, p.appointment
                              FROM Employees e
                              LEFT JOIN Positions p ON e.position_id = p.id_position
                              ORDER BY p.appointment, e.last_name;""")
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 70 + "\n"
            report_text += "ОТЧЕТ ПО СОТРУДНИКАМ АВТОПАРКА\n"
            report_text += "=" * 70 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего сотрудников: {len(rows)}\n\n"

            positions_dict = {}
            for row in rows:
                position = row[6] if row[6] else "Не указана"
                if position not in positions_dict:
                    positions_dict[position] = []
                positions_dict[position].append(row)

            for position, employees in positions_dict.items():
                report_text += f"\n{position.upper()}:\n"
                report_text += "-" * 50 + "\n"
                for emp in employees:
                    full_name = f"{emp[1]} {emp[2]} {emp[3]}".strip()
                    report_text += f"ID: {emp[0]} | {full_name}\n"
                    report_text += f"   Телефон: {emp[4]}\n"
                    if emp[5]:
                        report_text += f"   Email: {emp[5]}\n"
                report_text += f"Всего: {len(employees)} чел.\n"

            success, message = save_report(report_text, "employees_report")
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
        preview.setWindowTitle("Просмотр отчета - Сотрудники")
        preview.resize(650, 550)

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