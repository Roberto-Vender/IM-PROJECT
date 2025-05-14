import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QComboBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt


class Fill(QtWidgets.QDialog):
    def __init__(self):
        super(Fill, self).__init__()
        loadUi("Fill.ui", self)

        self.ticket_number = 1

        self.tableWidget = self.findChild(QtWidgets.QTableWidget, "tableWidget")
        self.combo_box = self.findChild(QComboBox, "combo_box1")
        self.gtvbutton = self.findChild(QtWidgets.QPushButton, "gtvbutton")
        self.submitbutton = self.findChild(QtWidgets.QPushButton, "submitbutton")
        self.cancelbutton = self.findChild(QtWidgets.QPushButton, "cancelbutton")
        self.btnToggleCalendar = self.findChild(QtWidgets.QPushButton, "btnToggleCalendar")
        self.calendarWidget = self.findChild(QtWidgets.QCalendarWidget, "calendarWidget")
        self.viewbutton = self.findChild(QtWidgets.QPushButton, "viewbutton")

        self.calendarWidget.hide()
        self.btnToggleCalendar.clicked.connect(self.toggle_calendar)

        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["Ticket Number", "Status", "Service Type", "Action"])
        self.tableWidget.setColumnWidth(0, 125)
        self.tableWidget.setColumnWidth(1, 140)
        self.tableWidget.setColumnWidth(2, 125)
        self.tableWidget.setColumnWidth(3, 100)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.submitbutton.clicked.connect(self.click_submit)
        self.cancelbutton.clicked.connect(self.click_cancel)
        self.viewbutton.clicked.connect(self.open_view)

        self.view_window = None

    def toggle_calendar(self):
        if self.calendarWidget.isVisible():
            self.calendarWidget.hide()
            self.btnToggleCalendar.setText("Select Date")
        else:
            self.calendarWidget.show()
            self.btnToggleCalendar.setText("Hide Calendar")

    def click_submit(self):
        row_position = self.tableWidget.rowCount()

        if self.ticket_number == 2:
            first_ticket_item = self.tableWidget.item(0, 0)
            first_status_combo = self.tableWidget.cellWidget(0, 1)
            first_status = first_status_combo.currentText() if first_status_combo else ""

            if first_ticket_item and first_ticket_item.text() == "Ticket Number: 1" and first_status == "Waiting":
                QtWidgets.QMessageBox.critical(self, "Error", "Ticket 1 must be admitted before creating Ticket 2.")
                return

        self.tableWidget.insertRow(row_position)

        ticket_item = QtWidgets.QTableWidgetItem(f"Ticket Number: {self.ticket_number}")
        self.tableWidget.setItem(row_position, 0, ticket_item)

        status_combo = QComboBox()
        status_combo.addItems(["Waiting", "Admit"])
        self.tableWidget.setCellWidget(row_position, 1, status_combo)
        self.set_combo_color(status_combo)
        status_combo.currentIndexChanged.connect(lambda index, row=row_position: self.status_changed(index, row))

        selected_service = self.combo_box.currentText()
        service_item = QtWidgets.QTableWidgetItem(selected_service)
        self.tableWidget.setItem(row_position, 2, service_item)

        done_button = QtWidgets.QPushButton("Done")
        done_button.clicked.connect(lambda _, r=row_position: self.mark_done(r))
        self.tableWidget.setCellWidget(row_position, 3, done_button)

        if self.view_window:
            ticket_number_text = str(self.ticket_number).zfill(3)
            if self.ticket_number == 1:
                self.view_window.promote_to_admit(ticket_number_text, selected_service)
            else:
                self.view_window.add_waiting_ticket(ticket_number_text, selected_service)

        self.ticket_number += 1

    def set_combo_color(self, combo_box):
        text = combo_box.currentText()
        if text == "Waiting":
            combo_box.setStyleSheet("QComboBox { background-color: red; color: white; }")
        elif text == "Admit":
            combo_box.setStyleSheet("QComboBox { background-color: green; color: white; }")
        else:
            combo_box.setStyleSheet("")

    def open_view(self):
        if not self.view_window:
            self.view_window = View()
        self.view_window.show()

    def click_cancel(self):
        selected_ranges = self.tableWidget.selectedRanges()
        if selected_ranges:
            row_index = selected_ranges[0].topRow()
            ticket_item = self.tableWidget.item(row_index, 0)
            if ticket_item:
                ticket_number = ticket_item.text().replace("Ticket Number: ", "").zfill(3)
                if self.view_window:
                    self.view_window.remove_ticket(ticket_number)
            self.tableWidget.removeRow(row_index)

    def status_changed(self, index, row):
        status_combo = self.tableWidget.cellWidget(row, 1)
        status = status_combo.currentText()
        ticket_item = self.tableWidget.item(row, 0)
        service_item = self.tableWidget.item(row, 2)

        if ticket_item and service_item:
            ticket_number = ticket_item.text().replace("Ticket Number: ", "").zfill(3)
            service_text = service_item.text()

            if self.view_window:
                if status == "Admit":
                    self.view_window.ensure_ticket_exists(ticket_number, service_text)
                    self.view_window.promote_to_admit(ticket_number, service_text)

            self.set_combo_color(status_combo)

    def mark_done(self, row):
        ticket_item = self.tableWidget.item(row, 0)
        if ticket_item:
            ticket_number = ticket_item.text().replace("Ticket Number: ", "").zfill(3)
            if self.view_window:
                self.view_window.remove_ticket(ticket_number)

        self.tableWidget.removeRow(row)

        # Promote the next ticket in the waiting list to "Serving"
        for row_index in range(self.tableWidget.rowCount()):
            status_combo = self.tableWidget.cellWidget(row_index, 1)
            if isinstance(status_combo, QComboBox) and status_combo.currentText() == "Waiting":
                status_combo.setCurrentText("Admit")
                ticket_item = self.tableWidget.item(row_index, 0)
                service_item = self.tableWidget.item(row_index, 2)
                if ticket_item and service_item and self.view_window:
                    ticket_number = ticket_item.text().replace("Ticket Number: ", "").zfill(3)
                    service_text = service_item.text()
                    self.view_window.promote_to_admit(ticket_number, service_text)
                break

        # Shift tickets in the waiting list up in the View window
        if self.view_window:
            self.view_window.shift_waiting_up()

        # Reconnect signals for remaining rows
        for row_index in range(self.tableWidget.rowCount()):
            done_button = QtWidgets.QPushButton("Done")
            done_button.clicked.connect(lambda _, r=row_index: self.mark_done(r))
            self.tableWidget.setCellWidget(row_index, 3, done_button)

            status_combo = self.tableWidget.cellWidget(row_index, 1)
            if isinstance(status_combo, QComboBox):
                status_combo.currentIndexChanged.disconnect()
                status_combo.currentIndexChanged.connect(lambda index, row=row_index: self.status_changed(index, row))
                self.set_combo_color(status_combo)


class View(QtWidgets.QDialog):
    def __init__(self):
        super(View, self).__init__()
        loadUi("view.ui", self)

        self.labels = [
            self.findChild(QtWidgets.QLabel, f"label_ticket{i}") for i in range(1, 6)
        ]
        self.label_service = [
            self.findChild(QtWidgets.QLabel, f"label_service{i}") for i in range(1, 6)
        ]

        for label in self.labels + self.label_service:
            if label:
                label.setText("")

    def add_waiting_ticket(self, ticket_number, service_text):
        for ticket_label, service_label in zip(self.labels, self.label_service):
            if ticket_label and ticket_label.text() == "":
                ticket_label.setText(ticket_number)
                ticket_label.setAlignment(Qt.AlignCenter)
                if service_label:
                    service_label.setText(service_text)
                    service_label.setAlignment(Qt.AlignCenter)
                break

    def promote_to_admit(self, ticket_number, service_text):
        if self.labels[0]:
            self.labels[0].setText(ticket_number)
            self.labels[0].setAlignment(Qt.AlignCenter)
        if self.label_service[0]:
            self.label_service[0].setText(service_text)
            self.label_service[0].setAlignment(Qt.AlignCenter)

        for i in range(1, len(self.labels)):
            if self.labels[i] and self.labels[i].text() == ticket_number:
                self.labels[i].setText("")
                if self.label_service[i]:
                    self.label_service[i].setText("")
                break

        self.shift_waiting_up()

    def shift_waiting_up(self):
        for i in range(1, len(self.labels) - 1):
            if self.labels[i] and self.labels[i].text() == "":
                if self.labels[i + 1] and self.labels[i + 1].text() != "":
                    self.labels[i].setText(self.labels[i + 1].text())
                    self.labels[i].setAlignment(Qt.AlignCenter)

                    if self.label_service[i] and self.label_service[i + 1]:
                        self.label_service[i].setText(self.label_service[i + 1].text())
                        self.label_service[i].setAlignment(Qt.AlignCenter)

                    self.labels[i + 1].setText("")
                    if self.label_service[i + 1]:
                        self.label_service[i + 1].setText("")

    def ensure_ticket_exists(self, ticket_number, service_text):
        for ticket_label in self.labels:
            if ticket_label.text() == ticket_number:
                return
        self.add_waiting_ticket(ticket_number, service_text)

    def mark_no_show(self, ticket_number):
        for i in range(len(self.labels)):
            if self.labels[i] and self.labels[i].text() == ticket_number:
                self.labels[i].setText("No Show")
                self.labels[i].setAlignment(Qt.AlignCenter)
                if self.label_service[i]:
                    self.label_service[i].setText("")
                break
        self.shift_waiting_up()

    def remove_ticket(self, ticket_number):
        for i in range(len(self.labels)):
            if self.labels[i].text() == ticket_number:
                self.labels[i].setText("")
                self.labels[i].setAlignment(Qt.AlignCenter)
                if self.label_service[i]:
                    self.label_service[i].setText("")
                    self.label_service[i].setAlignment(Qt.AlignCenter)
                break
        self.shift_waiting_up()


# Run the application
app = QtWidgets.QApplication(sys.argv)
mainwindow = Fill()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(1100)
widget.setFixedHeight(650)
widget.show()
sys.exit(app.exec_())