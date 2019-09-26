from PyQt5.QtWidgets import QWidget, QLabel, QTableWidget, QPushButton, QCheckBox, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QHeaderView
import json
import os

class EditCommandsWindow(QWidget):
    def __init__(self, env):
        super().__init__()
        self.env = env
        self.commandsTable = QTableWidget(0,3)
        addButton = QPushButton(env.translate("button.add"))
        removeButton = QPushButton(env.translate("button.remove"))
        okButton = QPushButton(env.translate("button.ok"))
        cancelButton = QPushButton(env.translate("button.cancel"))

        self.commandsTable.setHorizontalHeaderLabels((env.translate("editCommandsWindow.text"),env.translate("editCommandsWindow.command"),env.translate("editCommandsWindow.terminal")))
        self.commandsTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.commandsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        addButton.clicked.connect(self.newRow)
        removeButton.clicked.connect(lambda: self.commandsTable.removeRow(self.commandsTable.currentRow()))
        okButton.clicked.connect(self.okButtonClicked)
        cancelButton.clicked.connect(self.close)
       
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(removeButton)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(QLabel("%url% - " + env.translate("executeCommand.label.url")))
        mainLayout.addWidget(QLabel("%path% - " + env.translate("executeCommand.label.path")))
        mainLayout.addWidget(QLabel("%directory% - " + env.translate("executeCommand.label.directory")))
        mainLayout.addWidget(QLabel("%filename% - " + env.translate("executeCommand.label.filename")))
        mainLayout.addWidget(QLabel("%selection% - " + env.translate("executeCommand.label.selection")))
        mainLayout.addWidget(self.commandsTable)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.setWindowTitle(env.translate("editCommandsWindow.title"))

    def openWindow(self):
        while (self.commandsTable.rowCount() > 0):
            self.commandsTable.removeRow(0)
        count = 0
        for i in self.env.commands:
            self.commandsTable.insertRow(count)
            self.commandsTable.setItem(count, 0,QTableWidgetItem(i[0]))
            self.commandsTable.setItem(count, 1,QTableWidgetItem(i[1]))
            checkbox = QCheckBox()
            checkbox.setChecked(i[2])
            self.commandsTable.setCellWidget(count,2,checkbox)
            count += 1
        self.show()
        self.setFocus(True)

    def newRow(self):
        self.commandsTable.insertRow(self.commandsTable.rowCount())
        self.commandsTable.setCellWidget(self.commandsTable.rowCount()-1,2,QCheckBox())

    def okButtonClicked(self):
        self.env.commands = []
        for i in range(self.commandsTable.rowCount()):
            try:
                name = self.commandsTable.item(i,0).text()
                command = self.commandsTable.item(i,1).text()
                terminal = bool(self.commandsTable.cellWidget(i,2).checkState())
                if name != "":
                    self.env.commands.append([name,command,terminal])
            except:
                pass
        with open(os.path.join(self.env.dataDir,"commands.json"), 'w', encoding='utf-8') as f:
            json.dump(self.env.commands, f, ensure_ascii=False, indent=4)
        self.env.mainWindow.updateExecuteMenu()
        self.close()
