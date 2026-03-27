import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QSpinBox, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt
from db_connection import get_connection
from report_functions import save_report


class MaintenanceStructureWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Структура ТО - Запчасти в техническом обслуживании")
        self.resize(900, 550)
        self.selected_id = None
        self.init_ui()
        self.load_data()
        self.load_combos()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Количество", "Запчасть", "ТО ID", "Тип работ"])
        self.table.cellClicked.connect(self.select_row)
        main_layout.addWidget(self.table)

        form_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Количество:"))
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(99999)
        self.quantity_input.setValue(1)
        row1.addWidget(self.quantity_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Запчасть:"))
        self.spare_part_combo = QComboBox()
        self.spare_part_combo.setMinimumWidth(300)
        row2.addWidget(self.spare_part_combo)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Техобслуживание:"))
        self.maintenance_combo = QComboBox()
        self.maintenance_combo.setMinimumWidth(400)
        row3.addWidget(self.maintenance_combo)
        form_layout.addLayout(row3)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_structure)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_structure)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_structure)
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

            cursor.execute("SELECT id_spare_part, type_sp FROM SpareParts ORDER BY type_sp")
            spare_parts = cursor.fetchall()
            self.spare_part_combo.clear()
            for sp in spare_parts:
                self.spare_part_combo.addItem(f"{sp[1]}", sp[0])

            cursor.execute("""SELECT m.id_maintenance, m.date_m, m.type_m,
                              c.brand || ' ' || c.model as car_name
                              FROM Maintenance m
                              LEFT JOIN Cars c ON m.car_id = c.id_car
                              ORDER BY m.date_m DESC""")
            maintenances = cursor.fetchall()
            self.maintenance_combo.clear()
            for maint in maintenances:
                display_text = f"ID:{maint[0]} | {maint[1]} | {maint[2]} | {maint[3]}"
                self.maintenance_combo.addItem(display_text, maint[0])
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
            cursor.execute("""SELECT ms.id_maintenance_structure, ms.quantity,
                              sp.type_sp, ms.maintenance_id, m.type_m
                              FROM MaintenanceStructure ms
                              LEFT JOIN SpareParts sp ON ms.spare_part_id = sp.id_spare_part
                              LEFT JOIN Maintenance m ON ms.maintenance_id = m.id_maintenance
                              ORDER BY ms.id_maintenance_structure;""")
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
            self.quantity_input.setValue(int(self.table.item(row, 1).text()))

            spare_part_name = self.table.item(row, 2).text()
            for i in range(self.spare_part_combo.count()):
                if self.spare_part_combo.itemText(i) == spare_part_name:
                    self.spare_part_combo.setCurrentIndex(i)
                    break

            maintenance_id = self.table.item(row, 3).text()
            for i in range(self.maintenance_combo.count()):
                if str(self.maintenance_combo.itemData(i)) == maintenance_id:
                    self.maintenance_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            pass

    def add_structure(self):
        quantity = self.quantity_input.value()
        spare_part_id = self.spare_part_combo.currentData()
        maintenance_id = self.maintenance_combo.currentData()

        if not spare_part_id or not maintenance_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запчасть и техобслуживание!")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO MaintenanceStructure (quantity, spare_part_id, maintenance_id)
                           VALUES (%s, %s, %s)""",
                           (quantity, spare_part_id, maintenance_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Запись добавлена!")
            self.clear_inputs()
            self.load_data()
            self.load_combos()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_structure(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись!")
            return

        quantity = self.quantity_input.value()
        spare_part_id = self.spare_part_combo.currentData()
        maintenance_id = self.maintenance_combo.currentData()

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""UPDATE MaintenanceStructure SET quantity = %s,
                           spare_part_id = %s, maintenance_id = %s
                           WHERE id_maintenance_structure = %s""",
                           (quantity, spare_part_id, maintenance_id, self.selected_id))
            conn.commit()
            QMessageBox.information(self, "Успех", "Данные обновлены!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_structure(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись!")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Удалить эту запись?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM MaintenanceStructure WHERE id_maintenance_structure = %s",
                           (self.selected_id,))
            conn.commit()
            QMessageBox.information(self, "Успех", "Запись удалена!")
            self.clear_inputs()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def clear_inputs(self):
        self.selected_id = None
        self.quantity_input.setValue(1)
        if self.spare_part_combo.count() > 0:
            self.spare_part_combo.setCurrentIndex(0)
        if self.maintenance_combo.count() > 0:
            self.maintenance_combo.setCurrentIndex(0)

    def generate_report(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT ms.id_maintenance_structure, ms.quantity,
                              sp.type_sp, m.date_m, m.type_m,
                              c.brand || ' ' || c.model as car_name
                              FROM MaintenanceStructure ms
                              LEFT JOIN SpareParts sp ON ms.spare_part_id = sp.id_spare_part
                              LEFT JOIN Maintenance m ON ms.maintenance_id = m.id_maintenance
                              LEFT JOIN Cars c ON m.car_id = c.id_car
                              ORDER BY m.date_m DESC, sp.type_sp;""")
            rows = cursor.fetchall()
            if not rows:
                QMessageBox.warning(self, "Внимание", "Нет данных для отчета!")
                return

            report_text = "=" * 70 + "\n"
            report_text += "ОТЧЕТ ПО СТРУКТУРЕ ТЕХНИЧЕСКОГО ОБСЛУЖИВАНИЯ\n"
            report_text += "=" * 70 + "\n\n"
            report_text += f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            report_text += f"Всего записей: {len(rows)}\n\n"

            maintenance_dict = {}
            for row in rows:
                maint_key = f"ТО ID: {row[3]} | {row[4]} | Авто: {row[5]}"
                if maint_key not in maintenance_dict:
                    maintenance_dict[maint_key] = []
                maintenance_dict[maint_key].append((row[0], row[1], row[2]))

            for maint_key, parts in maintenance_dict.items():
                report_text += f"\n{maint_key}\n"
                report_text += "-" * 60 + "\n"
                for part in parts:
                    report_text += f"  Запчасть: {part[2]} | Количество: {part[1]} шт.\n"
                report_text += f"  Итого позиций: {len(parts)}\n"

            success, message = save_report(report_text, "maintenance_structure_report")
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
        preview.setWindowTitle("Просмотр отчета - Структура ТО")
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