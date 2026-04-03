import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QSpinBox,
                             QDateEdit, QComboBox, QTextEdit)
from PyQt5.QtCore import QDate
from db_connection import get_connection
from report_functions import save_report


class RoutesWindow(QWidget):
    def __init__(self, role="employee"):
        super().__init__()
        self.role = role
        self.setWindowTitle(f"Управление маршрутами ({role})")
        self.resize(1000, 650)
        self.selected_id = None
        self.init_ui()
        self.load_data()
        self.load_combos()
        self.apply_role_restrictions()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Дата отправления", "Дата прибытия",
                                              "Пункт назначения", "Расход топлива (л)",
                                              "Водитель", "Сотрудник", "Автомобиль"])
        self.table.cellClicked.connect(self.select_row)
        main_layout.addWidget(self.table)

        form_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Дата отправления:"))
        self.departure_date_input = QDateEdit()
        self.departure_date_input.setDate(QDate.currentDate())
        self.departure_date_input.setCalendarPopup(True)
        row1.addWidget(self.departure_date_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Дата прибытия:"))
        self.arrival_date_input = QDateEdit()
        self.arrival_date_input.setDate(QDate.currentDate())
        self.arrival_date_input.setCalendarPopup(True)
        row2.addWidget(self.arrival_date_input)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Пункт назначения:"))
        self.destination_input = QLineEdit()
        self.destination_input.setPlaceholderText("г.Москва ул. Садовое кольцо д.10")
        row3.addWidget(self.destination_input)
        form_layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Расход топлива (л):"))
        self.fuel_input = QSpinBox()
        self.fuel_input.setMinimum(0)
        self.fuel_input.setMaximum(99999)
        self.fuel_input.setValue(0)
        row4.addWidget(self.fuel_input)
        form_layout.addLayout(row4)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Водитель:"))
        self.driver_combo = QComboBox()
        row5.addWidget(self.driver_combo)
        form_layout.addLayout(row5)

        row6 = QHBoxLayout()
        row6.addWidget(QLabel("Сотрудник (оформивший):"))
        self.employee_combo = QComboBox()
        row6.addWidget(self.employee_combo)
        form_layout.addLayout(row6)

        row7 = QHBoxLayout()
        row7.addWidget(QLabel("Автомобиль:"))
        self.car_combo = QComboBox()
        row7.addWidget(self.car_combo)
        form_layout.addLayout(row7)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_route)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_route)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_route)
        btn_layout.addWidget(self.delete_btn)

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

            cursor.execute("SELECT id_driver, last_name, first_name FROM Drivers ORDER BY id_driver")
            drivers = cursor.fetchall()
            self.driver_combo.clear()
            for driver in drivers:
                self.driver_combo.addItem(f"{driver[1]} {driver[2]}", driver[0])

            cursor.execute("""SELECT e.id_employee, e.last_name, e.first_name, p.appointment
                              FROM Employees e
                              LEFT JOIN Positions p ON e.position_id = p.id_position
                              WHERE p.appointment = 'Диспетчер' OR p.appointment = 'диспетчер'
                              ORDER BY e.last_name, e.first_name""")
            employees = cursor.fetchall()
            self.employee_combo.clear()

            if employees:
                for emp in employees:
                    self.employee_combo.addItem(f"{emp[1]} {emp[2]}", emp[0])
            else:
                self.employee_combo.addItem("Нет доступных диспетчеров", None)
                self.employee_combo.setEnabled(True)

            cursor.execute("""SELECT id_car, brand, model, status 
                              FROM Cars 
                              ORDER BY 
                                CASE status 
                                    WHEN 'свободен' THEN 1 
                                    WHEN 'рейс' THEN 2 
                                    WHEN 'техобслуживание' THEN 3 
                                    ELSE 4 
                                END, brand, model""")
            cars = cursor.fetchall()
            self.car_combo.clear()

            status_rus = {
                'свободен': 'свободен',
                'рейс': 'рейс',
                'техобслуживание': 'техобслуживание',
            }

            for car in cars:
                original_status = car[3].lower() if car[3] else 'свободен'
                display_status = status_rus.get(original_status, original_status)
                self.car_combo.addItem(f"{car[1]} {car[2]} [{display_status}]", car[0])

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
            cursor.execute("""SELECT r.id_routes, r.departure_date, r.arrival_date, r.destination,
                              r.fuel_consumption,
                              d.last_name || ' ' || d.first_name as driver_name,
                              e.last_name || ' ' || e.first_name as employee_name,
                              c.brand || ' ' || c.model as car_name
                              FROM Routes r
                              LEFT JOIN Drivers d ON r.driver_id = d.id_driver
                              LEFT JOIN Employees e ON r.employee_id = e.id_employee
                              LEFT JOIN Cars c ON r.car_id = c.id_car
                              ORDER BY r.departure_date DESC;""")
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
            dep_date_str = self.table.item(row, 1).text()
            dep_date = QDate.fromString(dep_date_str, "yyyy-MM-dd")
            if dep_date.isValid():
                self.departure_date_input.setDate(dep_date)

            arr_date_str = self.table.item(row, 2).text()
            arr_date = QDate.fromString(arr_date_str, "yyyy-MM-dd")
            if arr_date.isValid():
                self.arrival_date_input.setDate(arr_date)

            self.destination_input.setText(self.table.item(row, 3).text())
            self.fuel_input.setValue(int(self.table.item(row, 4).text()))

            driver_name = self.table.item(row, 5).text()
            for i in range(self.driver_combo.count()):
                if self.driver_combo.itemText(i) == driver_name:
                    self.driver_combo.setCurrentIndex(i)
                    break

            employee_name = self.table.item(row, 6).text()
            for i in range(self.employee_combo.count()):
                if self.employee_combo.itemText(i).startswith(employee_name):
                    self.employee_combo.setCurrentIndex(i)
                    break

            car_name = self.table.item(row, 7).text()
            for i in range(self.car_combo.count()):
                if self.car_combo.itemText(i).startswith(car_name):
                    self.car_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            print(f"Ошибка выбора строки: {e}")

    def add_route(self):
        departure_date = self.departure_date_input.date().toString("yyyy-MM-dd")
        arrival_date = self.arrival_date_input.date().toString("yyyy-MM-dd")
        destination = self.destination_input.text().strip()
        fuel = self.fuel_input.value()
        driver_id = self.driver_combo.currentData()
        employee_id = self.employee_combo.currentData()
        car_id = self.car_combo.currentData()

        if not destination:
            QMessageBox.warning(self, "Ошибка", "Введите пункт назначения!")
            return

        if not driver_id:
            QMessageBox.warning(self, "Ошибка", "Выберите водителя!")
            return

        if not employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника!")
            return

        if not car_id:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return

        if departure_date > arrival_date:
            QMessageBox.warning(self, "Ошибка", "Дата отправления не может быть позже даты прибытия!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO Routes (departure_date, arrival_date, destination,
                           fuel_consumption, driver_id, employee_id, car_id)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                           (departure_date, arrival_date, destination, fuel,
                            driver_id, employee_id, car_id))
            conn.commit()

            cursor.execute("UPDATE Cars SET status = 'рейс' WHERE id_car = %s", (car_id,))
            conn.commit()

            QMessageBox.information(self, "Успех", "Маршрут добавлен! Статус автомобиля изменён на 'рейс'")
            self.clear_inputs()
            self.load_data()
            self.load_combos()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_route(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите маршрут!")
            return

        departure_date = self.departure_date_input.date().toString("yyyy-MM-dd")
        arrival_date = self.arrival_date_input.date().toString("yyyy-MM-dd")
        destination = self.destination_input.text().strip()
        fuel = self.fuel_input.value()
        driver_id = self.driver_combo.currentData()
        employee_id = self.employee_combo.currentData()
        car_id = self.car_combo.currentData()

        if not destination:
            QMessageBox.warning(self, "Ошибка", "Введите пункт назначения!")
            return

        if departure_date > arrival_date:
            QMessageBox.warning(self, "Ошибка", "Дата отправления не может быть позже даты прибытия!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT car_id FROM Routes WHERE id_routes = %s", (self.selected_id,))
            old_car_id = cursor.fetchone()
            old_car_id = old_car_id[0] if old_car_id else None

            cursor.execute("""UPDATE Routes SET departure_date = %s, arrival_date = %s,
                           destination = %s, fuel_consumption = %s, driver_id = %s,
                           employee_id = %s, car_id = %s
                           WHERE id_routes = %s""",
                           (departure_date, arrival_date, destination, fuel,
                            driver_id, employee_id, car_id, self.selected_id))
            conn.commit()

            if old_car_id and old_car_id != car_id:
                cursor.execute("""SELECT COUNT(*) FROM Routes 
                                   WHERE car_id = %s AND id_routes != %s""",
                               (old_car_id, self.selected_id))
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute("UPDATE Cars SET status = 'свободен' WHERE id_car = %s", (old_car_id,))
                
                cursor.execute("UPDATE Cars SET status = 'рейс' WHERE id_car = %s", (car_id,))
                conn.commit()

            QMessageBox.information(self, "Успех", "Данные обновлены!")
            self.clear_inputs()
            self.load_data()
            self.load_combos()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_route(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите маршрут!")
            return

        reply = QMessageBox.question(self, "Подтверждение", 
                                     "Удалить этот маршрут? Статус автомобиля будет изменён на 'свободен'",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT car_id FROM Routes WHERE id_routes = %s", (self.selected_id,))
            car_id = cursor.fetchone()
            car_id = car_id[0] if car_id else None

            cursor.execute("DELETE FROM Routes WHERE id_routes = %s", (self.selected_id,))
            conn.commit()

            if car_id:
                cursor.execute("""SELECT COUNT(*) FROM Routes WHERE car_id = %s""", (car_id,))
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute("UPDATE Cars SET status = 'свободен' WHERE id_car = %s", (car_id,))
                    conn.commit()

            QMessageBox.information(self, "Успех", "Маршрут удалён! Статус автомобиля изменён на 'свободен'")
            self.clear_inputs()
            self.load_data()
            self.load_combos()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def clear_inputs(self):
        self.selected_id = None
        self.departure_date_input.setDate(QDate.currentDate())
        self.arrival_date_input.setDate(QDate.currentDate())
        self.destination_input.clear()
        self.fuel_input.setValue(0)
        if self.driver_combo.count() > 0:
            self.driver_combo.setCurrentIndex(0)
        if self.employee_combo.count() > 0:
            self.employee_combo.setCurrentIndex(0)
        if self.car_combo.count() > 0:
            self.car_combo.setCurrentIndex(0)

    def apply_role_restrictions(self):
        if self.role == "employee":
            self.add_btn.setEnabled(True)
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            self.departure_date_input.setEnabled(True)
            self.arrival_date_input.setEnabled(True)
            self.destination_input.setReadOnly(True)
            self.fuel_input.setEnabled(True)
            self.driver_combo.setEnabled(True)
            self.employee_combo.setEnabled(True)
            self.car_combo.setEnabled(True)

    def generate_report(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT r.id_routes, r.departure_date, r.arrival_date, r.destination,
                              r.fuel_consumption,
                              d.last_name || ' ' || d.first_name as driver_name,
                              e.last_name || ' ' || e.first_name as employee_name,
                              c.brand || ' ' || c.model as car_name
                              FROM Routes r
                              LEFT JOIN Drivers d ON r.driver_id = d.id_driver
                              LEFT JOIN Employees e ON r.employee_id = e.id_employee
                              LEFT JOIN Cars c ON r.car_id = c.id_car
                              ORDER BY r.departure_date DESC;""")
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 80 + "\n"
            report_text += "ОТЧЕТ ПО МАРШРУТАМ АВТОПАРКА\n"
            report_text += "=" * 80 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего маршрутов: {len(rows)}\n\n"

            total_fuel = sum(row[4] for row in rows)
            report_text += f"Общий расход топлива: {total_fuel} л\n"
            report_text += "=" * 80 + "\n\n"

            for row in rows:
                id_route, dep_date, arr_date, destination, fuel, driver, employee, car = row
                report_text += f"Маршрут ID: {id_route}\n"
                report_text += f"Дата отправления: {dep_date}\n"
                report_text += f"Дата прибытия: {arr_date}\n"
                report_text += f"Пункт назначения: {destination}\n"
                report_text += f"Расход топлива: {fuel} л\n"
                report_text += f"Водитель: {driver}\n"
                report_text += f"Оформил: {employee}\n"
                report_text += f"Автомобиль: {car}\n"
                report_text += "-" * 60 + "\n"

            success, message = save_report(report_text, "routes_report")
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
        preview.setWindowTitle("Просмотр отчета - Маршруты")
        preview.resize(700, 550)

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