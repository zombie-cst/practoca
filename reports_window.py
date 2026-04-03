from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QFrame,
                             QLabel, QMessageBox, QFileDialog, QTextEdit)
from PyQt5.QtCore import Qt
from db_connection import get_connection
from datetime import datetime


class ReportsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Отчеты")
        self.resize(500, 350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Генерация отчетов")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        label_acc = QLabel("Справочные отчеты:")
        label_acc.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(label_acc)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

        self.btn_cars = QPushButton("Отчет по автомобилям")
        self.btn_cars.clicked.connect(self.report_cars)
        layout.addWidget(self.btn_cars)

        self.btn_drivers = QPushButton("Отчет по водителям")
        self.btn_drivers.clicked.connect(self.report_drivers)
        layout.addWidget(self.btn_drivers)

        self.btn_employees = QPushButton("Отчет по сотрудникам")
        self.btn_employees.clicked.connect(self.report_employees)
        layout.addWidget(self.btn_employees)

        self.btn_spare_parts = QPushButton("Отчет по запчастям")
        self.btn_spare_parts.clicked.connect(self.report_spare_parts)
        layout.addWidget(self.btn_spare_parts)

        label_acc = QLabel("Операционные отчеты:")
        label_acc.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(label_acc)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        self.btn_routes = QPushButton("Отчет по маршрутам")
        self.btn_routes.clicked.connect(self.report_routes)
        layout.addWidget(self.btn_routes)

        self.btn_maintenance = QPushButton("Отчет по техобслуживанию")
        self.btn_maintenance.clicked.connect(self.report_maintenance)
        layout.addWidget(self.btn_maintenance)

        self.btn_maintenance_structure = QPushButton("Отчет по структуре ТО (запчасти в ТО)")
        self.btn_maintenance_structure.clicked.connect(self.report_maintenance_structure)
        layout.addWidget(self.btn_maintenance_structure)

        self.btn_fuel = QPushButton("Отчет по расходу топлива")
        self.btn_fuel.clicked.connect(self.report_fuel)
        layout.addWidget(self.btn_fuel)

        layout.addStretch()
        self.setLayout(layout)

    def save_report_file(self, report_text, default_filename):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{default_filename}_{timestamp}.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", filename, "Text Files (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                QMessageBox.information(self, "Успех", f"Отчет сохранен:\n{file_path}")
                self.show_report_preview(report_text, default_filename)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def show_report_preview(self, report_text, title_prefix):
        preview = QWidget()
        preview.setWindowTitle(f"Просмотр отчета - {title_prefix}")
        preview.resize(700, 550)

        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(report_text)
        text_edit.setReadOnly(True)
        text_edit.setFontFamily("Courier New")
        layout.addWidget(text_edit)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(preview.close)
        layout.addWidget(close_btn)
        preview.setLayout(layout)
        preview.show()

    def report_cars(self):
        """Отчет по автомобилям"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id_car, brand, model, year_release, car_mileage, status 
                FROM Cars 
                ORDER BY 
                    CASE status 
                        WHEN 'active' THEN 1 
                        WHEN 'maintenance' THEN 2 
                        WHEN 'repair' THEN 3 
                        WHEN 'decommissioned' THEN 4 
                        ELSE 5 
                    END, brand, model
            """)
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            status_rus = {
                'active': 'В работе',
                'maintenance': 'На ТО',
                'repair': 'В ремонте',
                'decommissioned': 'Списан'
            }

            report_text = "=" * 70 + "\n"
            report_text += "ОТЧЕТ ПО АВТОМОБИЛЯМ АВТОПАРКА\n"
            report_text += "=" * 70 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего автомобилей: {len(rows)}\n\n"

            status_counts = {}
            for row in rows:
                status = row[5]
                status_counts[status] = status_counts.get(status, 0) + 1

            report_text += "Статистика по статусам:\n"
            for status, count in status_counts.items():
                report_text += f"  {status_rus.get(status, status)}: {count} шт.\n"
            report_text += "=" * 70 + "\n\n"

            for row in rows:
                id_car, brand, model, year, mileage, status = row
                report_text += f"ID: {id_car} | {brand} {model}\n"
                report_text += f"   Год выпуска: {year} | Пробег: {mileage:,} км\n"
                report_text += f"   Статус: {status_rus.get(status, status)}\n"
                report_text += "-" * 50 + "\n"

            self.save_report_file(report_text, "cars_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def report_drivers(self):
        """Отчет по водителям"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id_driver, last_name, first_name, patronymic,
                       phone_number, experience, category
                FROM Drivers 
                ORDER BY experience DESC, last_name
            """)
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 70 + "\n"
            report_text += "ОТЧЕТ ПО ВОДИТЕЛЯМ АВТОПАРКА\n"
            report_text += "=" * 70 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего водителей: {len(rows)}\n\n"

            total_experience = sum(row[5] for row in rows)
            avg_experience = total_experience / len(rows) if rows else 0
            report_text += f"Средний стаж водителей: {avg_experience:.1f} лет\n"
            report_text += "=" * 70 + "\n\n"

            for row in rows:
                id_driver, last_name, first_name, patronymic, phone, exp, category = row
                full_name = f"{last_name} {first_name} {patronymic}".strip()
                report_text += f"ID: {id_driver} | {full_name}\n"
                report_text += f"   Телефон: {phone} | Стаж: {exp} лет\n"
                report_text += f"   Категория: {category}\n"
                report_text += "-" * 50 + "\n"

            self.save_report_file(report_text, "drivers_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def report_employees(self):
        """Отчет по сотрудникам"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT e.id_employee, e.last_name, e.first_name, e.patronymic,
                       e.phone_number, e.gmail, p.appointment
                FROM Employees e
                LEFT JOIN Positions p ON e.position_id = p.id_position
                ORDER BY p.appointment, e.last_name
            """)
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

            self.save_report_file(report_text, "employees_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def report_spare_parts(self):
        """Отчет по запчастям"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id_spare_part, type_sp, quantity 
                FROM SpareParts 
                ORDER BY type_sp
            """)
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 70 + "\n"
            report_text += "ОТЧЕТ ПО ЗАПАСНЫМ ЧАСТЯМ\n"
            report_text += "=" * 70 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего наименований: {len(rows)}\n\n"

            total_quantity = sum(row[2] for row in rows)
            report_text += f"Общее количество на складе: {total_quantity} шт.\n"
            report_text += "=" * 70 + "\n\n"

            for row in rows:
                id_part, name, quantity = row
                report_text += f"ID: {id_part} | {name}\n"
                report_text += f"   Количество: {quantity} шт.\n"
                report_text += "-" * 50 + "\n"

            self.save_report_file(report_text, "spare_parts_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def report_routes(self):
        """Отчет по маршрутам"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT r.id_routes, r.departure_date, r.arrival_date, r.destination,
                       r.fuel_consumption,
                       d.last_name || ' ' || d.first_name as driver_name,
                       e.last_name || ' ' || e.first_name as employee_name,
                       c.brand || ' ' || c.model as car_name
                FROM Routes r
                LEFT JOIN Drivers d ON r.driver_id = d.id_driver
                LEFT JOIN Employees e ON r.employee_id = e.id_employee
                LEFT JOIN Cars c ON r.car_id = c.id_car
                ORDER BY r.departure_date DESC
            """)
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
                delta = (arr_date - dep_date).days if hasattr(arr_date, 'days') else 0
                report_text += f"Маршрут ID: {id_route}\n"
                report_text += f"   Дата отправления: {dep_date}\n"
                report_text += f"   Дата прибытия: {arr_date} (в пути: {delta} дн.)\n"
                report_text += f"   Пункт назначения: {destination}\n"
                report_text += f"   Расход топлива: {fuel} л\n"
                report_text += f"   Водитель: {driver}\n"
                report_text += f"   Оформил: {employee}\n"
                report_text += f"   Автомобиль: {car}\n"
                report_text += "-" * 60 + "\n"

            self.save_report_file(report_text, "routes_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def report_maintenance(self):
        """Отчет по техобслуживанию"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT m.id_maintenance, m.date_m, m.type_m,
                       e.last_name || ' ' || e.first_name as employee_name,
                       c.brand || ' ' || c.model as car_name,
                       (SELECT COUNT(*) FROM MaintenanceStructure 
                        WHERE maintenance_id = m.id_maintenance) as parts_count
                FROM Maintenance m
                LEFT JOIN Employees e ON m.employee_id = e.id_employee
                LEFT JOIN Cars c ON m.car_id = c.id_car
                ORDER BY m.date_m DESC
            """)
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 80 + "\n"
            report_text += "ОТЧЕТ ПО ТЕХНИЧЕСКОМУ ОБСЛУЖИВАНИЮ\n"
            report_text += "=" * 80 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего записей: {len(rows)}\n\n"

            for row in rows:
                id_m, date, type_m, employee, car, parts_count = row
                report_text += f"ТО ID: {id_m}\n"
                report_text += f"   Дата: {date}\n"
                report_text += f"   Тип работ: {type_m}\n"
                report_text += f"   Ответственный (механик): {employee}\n"
                report_text += f"   Автомобиль: {car}\n"
                report_text += f"   Использовано запчастей: {parts_count} наименований\n"
                report_text += "-" * 60 + "\n"

            self.save_report_file(report_text, "maintenance_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def report_maintenance_structure(self):
        """Отчет по структуре ТО (запчасти, использованные в ТО)"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT ms.id_maintenance_structure, ms.quantity,
                       sp.type_sp, m.date_m, m.type_m,
                       c.brand || ' ' || c.model as car_name
                FROM MaintenanceStructure ms
                LEFT JOIN SpareParts sp ON ms.spare_part_id = sp.id_spare_part
                LEFT JOIN Maintenance m ON ms.maintenance_id = m.id_maintenance
                LEFT JOIN Cars c ON m.car_id = c.id_car
                ORDER BY m.date_m DESC, m.id_maintenance, sp.type_sp
            """)
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 80 + "\n"
            report_text += "ОТЧЕТ ПО СТРУКТУРЕ ТЕХНИЧЕСКОГО ОБСЛУЖИВАНИЯ\n"
            report_text += "=" * 80 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего записей об использовании запчастей: {len(rows)}\n\n"

            maintenance_dict = {}
            for row in rows:
                maint_key = f"ТО ID: {row[3]} | {row[4]} | Авто: {row[5]}"
                if maint_key not in maintenance_dict:
                    maintenance_dict[maint_key] = []
                maintenance_dict[maint_key].append((row[0], row[1], row[2]))

            for maint_key, parts in maintenance_dict.items():
                report_text += f"\n{maint_key}\n"
                report_text += "-" * 70 + "\n"
                for part in parts:
                    report_text += f"   Запчасть: {part[2]} | Количество: {part[1]} шт.\n"
                report_text += f"   Итого позиций: {len(parts)}\n"

            self.save_report_file(report_text, "maintenance_structure_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def report_fuel(self):
        """Отчет по расходу топлива"""
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT r.id_routes, r.departure_date, r.destination,
                       r.fuel_consumption,
                       d.last_name || ' ' || d.first_name as driver_name,
                       c.brand || ' ' || c.model as car_name
                FROM Routes r
                LEFT JOIN Drivers d ON r.driver_id = d.id_driver
                LEFT JOIN Cars c ON r.car_id = c.id_car
                ORDER BY r.departure_date DESC
            """)
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            total_fuel = sum(row[3] for row in rows)
            total_routes = len(rows)
            avg_fuel_per_route = total_fuel / total_routes if total_routes > 0 else 0

            report_text = "=" * 80 + "\n"
            report_text += "ОТЧЕТ ПО РАСХОДУ ТОПЛИВА\n"
            report_text += "=" * 80 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            report_text += "СВОДНАЯ СТАТИСТИКА:\n"
            report_text += "-" * 50 + "\n"
            report_text += f"Всего маршрутов: {total_routes}\n"
            report_text += f"Общий расход топлива: {total_fuel:,} л\n"
            report_text += f"Средний расход на маршрут: {avg_fuel_per_route:.2f} л\n"
            report_text += "=" * 80 + "\n\n"

            report_text += "ДЕТАЛИЗАЦИЯ ПО МАРШРУТАМ:\n"
            report_text += "-" * 80 + "\n\n"

            for row in rows:
                id_route, date, destination, fuel, driver, car = row
                report_text += f"Маршрут ID: {id_route}\n"
                report_text += f"   Дата: {date}\n"
                report_text += f"   Назначение: {destination}\n"
                report_text += f"   Расход топлива: {fuel} л\n"
                report_text += f"   Водитель: {driver}\n"
                report_text += f"   Автомобиль: {car}\n"
                report_text += "-" * 60 + "\n"

            self.save_report_file(report_text, "fuel_report")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
        finally:
            cursor.close()
            conn.close()