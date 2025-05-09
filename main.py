import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QComboBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, uic


class Fill(QtWidgets.QDialog):
    def __init__(self):
        super(Fill, self).__init__()
        loadUi("Fill.ui", self)

        # Start ticket from 1
        self.ticket_number = 1

        # Find widgets
        self.tableWidget = self.findChild(QtWidgets.QTableWidget, "tableWidget")
        self.combo_box = self.findChild(QComboBox, "combo_box1")
        self.gtvbutton = self.findChild(QtWidgets.QPushButton, "gtvbutton")
        self.submitbutton = self.findChild(QtWidgets.QPushButton, "submitbutton")
        self.cancelbutton = self.findChild(QtWidgets.QPushButton, "cancelbutton")
        self.calendarWidget = self.findChild(QtWidgets.QCalendarWidget, "calendarWidget")
        self.btnToggleCalendar = self.findChild(QtWidgets.QPushButton, "btnToggleCalendar")

        # Hide calendar at startup
        self.calendarWidget.hide()

        # Connect calendar toggle button
        self.btnToggleCalendar.clicked.connect(self.toggle_calendar)

        # Create table
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["Ticket Number", "Status", "Service Type"])
        self.tableWidget.setColumnWidth(0, 125)
        self.tableWidget.setColumnWidth(1, 140)
        self.tableWidget.setColumnWidth(2, 125)

        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Connect buttons
        self.submitbutton.clicked.connect(self.click_submit)
        self.viewbutton.clicked.connect(self.open_view)
        self.cancelbutton.clicked.connect(self.click_cancel)

        self.view_window = None
    #calendar
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
        status_combo.addItems(["Waiting", "Admit",])
        self.tableWidget.setCellWidget(row_position, 1, status_combo)
        self.set_combo_color(status_combo)
        status_combo.currentIndexChanged.connect(lambda index, row=row_position: self.status_changed(index, row))

        selected_service = self.combo_box.currentText()
        service_item = QtWidgets.QTableWidgetItem(selected_service)
        self.tableWidget.setItem(row_position, 2, service_item)

        # ✨ Add waiting ticket with service
        if self.view_window:
            ticket_number_text = str(self.ticket_number).zfill(3)
            self.view_window.add_waiting_ticket(ticket_number_text, selected_service)

        #Ticket increment +1
        self.ticket_number += 1

    #Admit and waiting color
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

            # Get ticket number before removing row
            ticket_item = self.tableWidget.item(row_index, 0)
            if ticket_item:
                ticket_number = ticket_item.text().replace("Ticket Number: ", "").zfill(3)

                # Inform the view to remove it too
                if self.view_window:
                    self.view_window.remove_ticket(ticket_number)

            # Now remove the row
            self.tableWidget.removeRow(row_index)

    # In Fill class
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


# View window class
class View(QtWidgets.QDialog):
    def __init__(self):
        super(View, self).__init__()
        loadUi("view.ui", self)

        self.labels = [
            self.findChild(QtWidgets.QLabel, "label_ticket1"),
            self.findChild(QtWidgets.QLabel, "label_ticket2"),
            self.findChild(QtWidgets.QLabel, "label_ticket3"),
            self.findChild(QtWidgets.QLabel, "label_ticket4"),
            self.findChild(QtWidgets.QLabel, "label_ticket5"),
        ]

        self.label_service = [
            self.findChild(QtWidgets.QLabel, "label_service1"),
            self.findChild(QtWidgets.QLabel, "label_service2"),
            self.findChild(QtWidgets.QLabel, "label_service3"),
            self.findChild(QtWidgets.QLabel, "label_service4"),
            self.findChild(QtWidgets.QLabel, "label_service5"),
        ]

        for label in self.labels:
            if label:
                label.setText("")

        for label in self.label_service:
            if label:
                label.setText("")


    def add_waiting_ticket(self, ticket_number, service_text):
        # Find the first empty slot to add ticket and service
        for ticket_label, service_label in zip(self.labels, self.label_service):
            if ticket_label and ticket_label.text() == "":
                ticket_label.setText(ticket_number)
                ticket_label.setAlignment(Qt.AlignCenter)

                if service_label:
                    service_label.setText(service_text)
                    service_label.setAlignment(Qt.AlignCenter)
                break

    def promote_to_admit(self, ticket_number, service_text):
        # Move the admitted ticket to label_ticket1
        if self.labels[0]:
            self.labels[0].setText(ticket_number)
            self.labels[0].setAlignment(Qt.AlignCenter)
        if self.label_service[0]:
            self.label_service[0].setText(service_text)
            self.label_service[0].setAlignment(Qt.AlignCenter)

        # Now remove the ticket from wherever it was waiting (label_ticket2-5)
        for i in range(1, len(self.labels)):
            if self.labels[i] and self.labels[i].text() == ticket_number:
                self.labels[i].setText("")
                if self.label_service[i]:
                    self.label_service[i].setText("")
                break

        # After removing, shift all waiting tickets up
        self.shift_waiting_up()

    def shift_waiting_up(self):
        # Shift all tickets from label_ticket2 to label_ticket5 upwards
        for i in range(1, len(self.labels) - 1):
            if self.labels[i] and self.labels[i].text() == "":
                if self.labels[i + 1] and self.labels[i + 1].text() != "":
                    self.labels[i].setText(self.labels[i + 1].text())
                    self.labels[i].setAlignment(Qt.AlignCenter)

                    if self.label_service[i] and self.label_service[i + 1]:
                        self.label_service[i].setText(self.label_service[i + 1].text())
                        self.label_service[i].setAlignment(Qt.AlignCenter)

                    # Clear the next one after moving
                    self.labels[i + 1].setText("")
                    if self.label_service[i + 1]:
                        self.label_service[i + 1].setText("")

    # In View class
    def ensure_ticket_exists(self, ticket_number, service_text):
        for ticket_label in self.labels:
            if ticket_label.text() == ticket_number:
                return

        self.add_waiting_ticket(ticket_number, service_text)

    def mark_no_show(self, ticket_number):
        # Find and clear the ticket if marked as no show
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


# Start the application
app = QtWidgets.QApplication(sys.argv)
mainwindow = Fill()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(1100)
widget.setFixedHeight(650)
widget.show()
sys.exit(app.exec_())
