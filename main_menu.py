from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFrame)
from cars_window import CarsWindow
from drivers_window import DriversWindow
from employees_window import EmployeesWindow
from routes_window import RoutesWindow
from maintenance_window import MaintenanceWindow
from spare_parts_window import SparePartsWindow
from maintenance_structure_window import MaintenanceStructureWindow
from reports_window import ReportsWindow
from change_password_window import ChangePasswordWindow
from admin_panel import AdminPanel


class MainMenu(QWidget):
    def __init__(self, username, role):
        super().__init__()
        self.username = username
        self.role = role
        self.setWindowTitle(f"Главное меню - Автопарк ({role})")
        self.resize(500, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        user_info = QLabel(f"Пользователь: {self.username}\nРоль: {self.role}")
        user_info.setStyleSheet("font-size: 14px; margin: 10px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(user_info)

        label_sprav = QLabel("Справочнки:")
        label_sprav.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(label_sprav)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

        self.btn_cars = QPushButton("Автомобили")
        self.btn_cars.clicked.connect(self.open_cars)
        layout.addWidget(self.btn_cars)

        self.btn_drivers = QPushButton("Водители")
        self.btn_drivers.clicked.connect(self.open_drivers)
        layout.addWidget(self.btn_drivers)

        self.btn_employees = QPushButton("Сотрудники")
        self.btn_employees.clicked.connect(self.open_employees)
        layout.addWidget(self.btn_employees)

        self.btn_spare_parts = QPushButton("Запчасти")
        self.btn_spare_parts.clicked.connect(self.open_spare_parts)
        layout.addWidget(self.btn_spare_parts)

        self.btn_maintenance_structure = QPushButton("Структура ТО")
        self.btn_maintenance_structure.clicked.connect(self.open_maintenance_structure)
        layout.addWidget(self.btn_maintenance_structure)

        layout.addSpacing(10)

        label_oper = QLabel("Операции:")
        label_oper.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(label_oper)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        self.btn_routes = QPushButton("Маршруты")
        self.btn_routes.clicked.connect(self.open_routes)
        layout.addWidget(self.btn_routes)

        self.btn_maintenance = QPushButton("Техобслуживание")
        self.btn_maintenance.clicked.connect(self.open_maintenance)
        layout.addWidget(self.btn_maintenance)

        self.btn_reports = QPushButton("Отчёты")
        self.btn_reports.clicked.connect(self.open_reports)
        layout.addWidget(self.btn_reports)

        layout.addSpacing(10)

        label_acc = QLabel("Остальное:")
        label_acc.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(label_acc)

        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line3)

        self.btn_change_password = QPushButton("Сменить пароль")
        self.btn_change_password.clicked.connect(self.open_change_password)
        layout.addWidget(self.btn_change_password)

        if self.role == "admin":
            self.btn_admin_panel = QPushButton("Панель администратора")
            self.btn_admin_panel.clicked.connect(self.open_admin_panel)
            layout.addWidget(self.btn_admin_panel)

        self.btn_exit = QPushButton("Выйти из системы")
        self.btn_exit.clicked.connect(self.close)
        layout.addWidget(self.btn_exit)

        self.apply_role_restrictions()
        self.setLayout(layout)

    def apply_role_restrictions(self):
        if self.role == "employee":
            self.btn_employees.setEnabled(False)
            self.btn_spare_parts.setEnabled(True)
            self.btn_maintenance_structure.setEnabled(True)
            self.btn_cars.setEnabled(True)
            self.btn_drivers.setEnabled(True)
            self.btn_routes.setEnabled(True)
            self.btn_maintenance.setEnabled(True)
            self.btn_reports.setEnabled(True)

    def open_cars(self):
        self.cars_window = CarsWindow(self.role)
        self.cars_window.show()

    def open_drivers(self):
        self.drivers_window = DriversWindow(self.role)
        self.drivers_window.show()

    def open_employees(self):
        if self.role != "admin":
            QMessageBox.warning(self, "Доступ запрещён", "У вас нет прав для управления сотрудниками!")
            return
        self.employees_window = EmployeesWindow()
        self.employees_window.show()

    def open_routes(self):
        self.routes_window = RoutesWindow(self.role)
        self.routes_window.show()

    def open_maintenance(self):
        self.maintenance_window = MaintenanceWindow(self.role)
        self.maintenance_window.show()

    def open_spare_parts(self):
        self.spare_parts_window = SparePartsWindow()
        self.spare_parts_window.show()

    def open_maintenance_structure(self):
        self.maintenance_structure_window = MaintenanceStructureWindow()
        self.maintenance_structure_window.show()

    def open_reports(self):
        self.reports_window = ReportsWindow()
        self.reports_window.show()

    def open_change_password(self):
        self.change_password_window = ChangePasswordWindow(self.username)
        self.change_password_window.show()

    def open_admin_panel(self):
        self.admin_panel = AdminPanel()
        self.admin_panel.show()