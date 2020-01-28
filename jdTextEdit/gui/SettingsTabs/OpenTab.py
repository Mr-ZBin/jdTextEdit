from PyQt5.QtWidgets import QWidget, QCheckBox, QComboBox, QLabel, QHBoxLayout, QVBoxLayout
from jdTextEdit.Functions import selectComboBoxItem

class OpenTab(QWidget):
    def __init__(self, env):
        super().__init__()
        self.useIPCCheckBox = QCheckBox(env.translate("settingsWindow.open.checkBox.useIPC"))
        self.detectLanguage = QCheckBox(env.translate("settingsWindow.open.checkBox.detectLanguage"))
        self.detectEol = QCheckBox(env.translate("settingsWindow.open.checkBox.detectEol"))
        self.detectEncoding = QCheckBox(env.translate("settingsWindow.open.checkBox.detectEncoding"))
        self.detectLibComboBox = QComboBox()

        for key, value in env.encodingDetectFunctions.items():
            self.detectLibComboBox.addItem(key)

        detectLibLayout = QHBoxLayout()
        detectLibLayout.addWidget(QLabel(env.translate("settingsWindow.open.label.encodingDetectLib")))
        detectLibLayout.addWidget(self.detectLibComboBox)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.useIPCCheckBox)
        mainLayout.addWidget(self.detectLanguage)
        mainLayout.addWidget(self.detectEol)
        mainLayout.addWidget(self.detectEncoding)
        mainLayout.addLayout(detectLibLayout)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

    def updateTab(self, settings):
        self.useIPCCheckBox.setChecked(settings.useIPC)
        self.detectLanguage.setChecked(settings.detectLanguage)
        self.detectEol.setChecked(settings.detectEol)
        self.detectEncoding.setChecked(settings.detectEncoding)
        selectComboBoxItem(self.detectLibComboBox,settings.encodingDetectLib)

    def getSettings(self, settings):
        settings.useIPC = bool(self.useIPCCheckBox.checkState())
        settings.detectLanguage = bool(self.detectLanguage.checkState())
        settings.detectEncoding = bool(self.detectEncoding.checkState())
        settings.detectEol = bool(self.detectEol.checkState())
        settings.encodingDetectLib = self.detectLibComboBox.itemText(self.detectLibComboBox.currentIndex())
        return settings
