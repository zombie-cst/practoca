import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QDateEdit,
                             QComboBox, QTextEdit, QSpinBox, QDialog,
                             QDialogButtonBox)
from PyQt5.QtCore import QDate
from db_connection import get_connection
from report_functions import save_report


class MaintenanceWindow(QWidget):
    def __init__(self, role="employee"):
        super().__init__()
        self.role = role
        self.setWindowTitle(f"Управление техобслуживанием ({role})")
        self.resize(1100, 650)
        self.selected_id = None
        self.init_ui()
        self.load_data()
        self.load_combos()
        self.apply_role_restrictions()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Тип работ",
                                              "Сотрудник (механик)", "Автомобиль", "Исп. запчасти"])
        self.table.cellClicked.connect(self.select_row)
        main_layout.addWidget(self.table)

        form_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Дата:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        row1.addWidget(self.date_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Тип работ:"))
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Замена масла, ремонт двигателя и т.д.")
        row2.addWidget(self.type_input)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Механик:"))
        self.employee_combo = QComboBox()
        row3.addWidget(self.employee_combo)
        form_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Автомобиль:"))
        self.car_combo = QComboBox()
        row4.addWidget(self.car_combo)
        form_layout.addLayout(row4)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_maintenance)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_maintenance)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_maintenance)
        btn_layout.addWidget(self.delete_btn)

        self.view_parts_btn = QPushButton("Просмотр запчастей в ТО")
        self.view_parts_btn.clicked.connect(self.view_parts)
        btn_layout.addWidget(self.view_parts_btn)

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)

        self.report_btn = QPushButton("Создать отчет")
        self.report_btn.clicked.connect(self.generate_report)
        btn_layout.addWidget(self.report_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_combos(self):
        conn = get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()

            cursor.execute("""SELECT e.id_employee, e.last_name, e.first_name, p.appointment
                              FROM Employees e
                              LEFT JOIN Positions p ON e.position_id = p.id_position
                              WHERE p.appointment = 'Механик' OR p.appointment = 'механик'
                              ORDER BY e.last_name, e.first_name""")
            employees = cursor.fetchall()
            self.employee_combo.clear()

            if employees:
                for emp in employees:
                    self.employee_combo.addItem(f"{emp[1]} {emp[2]}", emp[0])
            else:
                self.employee_combo.addItem("Нет доступных механиков", None)
                self.employee_combo.setEnabled(False)

            cursor.execute("""SELECT id_car, brand, model, status 
                              FROM Cars 
                              ORDER BY 
                                CASE status 
                                    WHEN 'active' THEN 1 
                                    WHEN 'maintenance' THEN 2 
                                    WHEN 'repair' THEN 3 
                                    WHEN 'decommissioned' THEN 4 
                                    ELSE 5 
                                END, brand, model""")
            cars = cursor.fetchall()
            self.car_combo.clear()

            status_rus = {
                'active': 'В работе',
                'maintenance': 'На ТО',
                'repair': 'В ремонте',
                'decommissioned': 'Списан'
            }

            for car in cars:
                status_text = status_rus.get(car[3], car[3])
                self.car_combo.addItem(f"{car[1]} {car[2]} [{status_text}]", car[0])

        except Exception as e:
            print(f"Ошибка загрузки комбобоксов: {e}")
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
            cursor.execute("""SELECT m.id_maintenance, m.date_m, m.type_m,
                              e.last_name || ' ' || e.first_name as employee_name,
                              c.brand || ' ' || c.model as car_name,
                              (SELECT COUNT(*) FROM MaintenanceStructure 
                               WHERE maintenance_id = m.id_maintenance) as parts_count
                              FROM Maintenance m
                              LEFT JOIN Employees e ON m.employee_id = e.id_employee
                              LEFT JOIN Cars c ON m.car_id = c.id_car
                              ORDER BY m.date_m DESC;""")
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
            date_str = self.table.item(row, 1).text()
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if date.isValid():
                self.date_input.setDate(date)
            self.type_input.setText(self.table.item(row, 2).text())

            employee_name = self.table.item(row, 3).text()
            for i in range(self.employee_combo.count()):
                if self.employee_combo.itemText(i) == employee_name:
                    self.employee_combo.setCurrentIndex(i)
                    break

            car_name = self.table.item(row, 4).text()
            for i in range(self.car_combo.count()):
                if self.car_combo.itemText(i).startswith(car_name):
                    self.car_combo.setCurrentIndex(i)
                    break
        except Exception:
            pass

    def add_maintenance(self):
        date = self.date_input.date().toString("yyyy-MM-dd")
        type_m = self.type_input.text().strip()
        employee_id = self.employee_combo.currentData()
        car_id = self.car_combo.currentData()

        if not type_m:
            QMessageBox.warning(self, "Ошибка", "Введите тип работ!")
            return

        if not employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите механика!")
            return

        if not car_id:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO Maintenance (date_m, type_m, employee_id, car_id)
                           VALUES (%s, %s, %s, %s) RETURNING id_maintenance""",
                           (date, type_m, employee_id, car_id))
            new_id = cursor.fetchone()[0]
            conn.commit()
            QMessageBox.information(self, "Успех", f"Запись о ТО добавлена! ID: {new_id}")
            self.clear_inputs()
            self.load_data()
            self.load_combos()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_maintenance(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись!")
            return

        date = self.date_input.date().toString("yyyy-MM-dd")
        type_m = self.type_input.text().strip()
        employee_id = self.employee_combo.currentData()
        car_id = self.car_combo.currentData()

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""UPDATE Maintenance SET date_m = %s, type_m = %s,
                           employee_id = %s, car_id = %s WHERE id_maintenance = %s""",
                           (date, type_m, employee_id, car_id, self.selected_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Данные обновлены!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_maintenance(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись!")
            return

        reply = QMessageBox.question(self, "Подтверждение", 
                                     "Удалить эту запись? Все связанные запчасти в структуре ТО также будут удалены!",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM MaintenanceStructure WHERE maintenance_id = %s", (self.selected_id,))
            cursor.execute("DELETE FROM Maintenance WHERE id_maintenance = %s", (self.selected_id,))
            conn.commit()
            QMessageBox.information(self, "Успех", "Запись удалена!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def view_parts(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись ТО!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT ms.id_maintenance_structure, ms.quantity, sp.type_sp
                              FROM MaintenanceStructure ms
                              LEFT JOIN SpareParts sp ON ms.spare_part_id = sp.id_spare_part
                              WHERE ms.maintenance_id = %s
                              ORDER BY sp.type_sp;""", (self.selected_id,))
            rows = cursor.fetchall()

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Запчасти в ТО #{self.selected_id}")
            dialog.resize(500, 400)

            layout = QVBoxLayout()

            if rows:
                table = QTableWidget()
                table.setColumnCount(3)
                table.setHorizontalHeaderLabels(["ID", "Количество", "Запчасть"])
                table.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    for j, val in enumerate(row):
                        table.setItem(i, j, QTableWidgetItem(str(val)))
                table.resizeColumnsToContents()
                layout.addWidget(table)
            else:
                layout.addWidget(QLabel("В этом ТО нет запчастей."))

            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)

            dialog.setLayout(layout)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def clear_inputs(self):
        self.selected_id = None
        self.date_input.setDate(QDate.currentDate())
        self.type_input.clear()
        if self.employee_combo.count() > 0:
            self.employee_combo.setCurrentIndex(0)
        if self.car_combo.count() > 0:
            self.car_combo.setCurrentIndex(0)

    def apply_role_restrictions(self):
        if self.role == "employee":
            self.add_btn.setEnabled(False)
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.view_parts_btn.setEnabled(True)
            self.clear_btn.setEnabled(False)
            self.date_input.setEnabled(False)
            self.type_input.setReadOnly(True)
            self.employee_combo.setEnabled(False)
            self.car_combo.setEnabled(False)

    def generate_report(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT m.id_maintenance, m.date_m, m.type_m,
                              e.last_name || ' ' || e.first_name as employee_name,
                              c.brand || ' ' || c.model as car_name,
                              (SELECT COUNT(*) FROM MaintenanceStructure 
                               WHERE maintenance_id = m.id_maintenance) as parts_count
                              FROM Maintenance m
                              LEFT JOIN Employees e ON m.employee_id = e.id_employee
                              LEFT JOIN Cars c ON m.car_id = c.id_car
                              ORDER BY m.date_m DESC;""")
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 70 + "\n"
            report_text += "ОТЧЕТ ПО ТЕХНИЧЕСКОМУ ОБСЛУЖИВАНИЮ\n"
            report_text += "=" * 70 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего записей: {len(rows)}\n\n"

            for row in rows:
                id_m, date, type_m, employee, car, parts_count = row
                report_text += f"ТО ID: {id_m}\n"
                report_text += f"Дата: {date}\n"
                report_text += f"Тип работ: {type_m}\n"
                report_text += f"Ответственный (механик): {employee}\n"
                report_text += f"Автомобиль: {car}\n"
                report_text += f"Использовано запчастей: {parts_count} наименований\n"
                report_text += "-" * 50 + "\n"

            success, message = save_report(report_text, "maintenance_report")
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
        preview.setWindowTitle("Просмотр отчета - Техобслуживание")
        preview.resize(600, 500)

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