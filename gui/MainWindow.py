from PyQt5.QtWidgets import QMainWindow, QMenu, QAction, QApplication, QLabel, QFileDialog, QStyleFactory, QStyle, QColorDialog
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QIcon, QTextDocument
from PyQt5.QtCore import Qt
from gui.DockWidget import DockWidget
from gui.EditTabWidget import EditTabWidget
from string import ascii_uppercase
from PyQt5.Qsci import QsciScintilla, QsciScintillaBase
from Functions import executeCommand, getThemeIcon, openFileDefault, showMessageBox, saveWindowState,restoreWindowState
from EncodingList import getEncodingList
from Updater import searchForUpdates
import traceback
import webbrowser
import requests
import tempfile
import shutil
import chardet
import json
import sys
import os
import re

class MainWindow(QMainWindow):
    def __init__(self,env):
        super().__init__()
        self.env = env
        self.setupMenubar()
        self.tabWidget = EditTabWidget(env)
        self.setupStatusBar()
        if os.path.isfile(os.path.join(env.dataDir,"session.json")):
            try:
                self.restoreSession()
            except Exception as e:
                print(traceback.format_exc(),end="")
                showMessageBox("Error","Could not restore session. If jdTextEdit crashes just restart it.")
                os.remove(os.path.join(self.env.dataDir,"session.json"))
                shutil.rmtree(os.path.join(self.env.dataDir,"session_data"))
            if len(env.args) == 1:
                self.tabWidget.createTab("",focus=True)
                self.openFile(os.path.abspath(env.args[0]))
        else:
            self.tabWidget.createTab(env.translate("mainWindow.newTabTitle"))
            if len(env.args) == 1:
                self.openFile(os.path.abspath(env.args[0]))
        self.toolbar = self.addToolBar("toolbar")
        self.setCentralWidget(self.tabWidget)
        if "MainWindow" in env.windowState:
            restoreWindowState(self,env.windowState,"MainWindow")
        else:
            self.setGeometry(0, 0, 800, 600)
 
    def setup(self):
        #This is called, after all at least
        self.getMenuActions(self.menubar)
        self.env.sidepane = DockWidget(self.env)
        self.env.sidepane.hide()
        self.addDockWidget(Qt.LeftDockWidgetArea,self.env.sidepane)
        for i in self.tabWidget.tabs:
            i[0].modificationStateChange(i[0].isModified())
        if self.env.settings.showSidepane:
            self.toggleSidebarClicked()
        self.env.sidepane.content.setCurrentWidget(self.env.settings.sidepaneWidget)
        self.getTextEditWidget().updateEolMenu()
        self.getTextEditWidget().updateEncodingMenu()
        self.env.settingsWindow.setup()
        self.env.dayTipWindow.setup()
        self.updateSettings(self.env.settings)
        if self.env.settings.searchUpdates:
            searchForUpdates(self.env,True)
        self.show()
        if self.env.settings.startupDayTip:
            self.env.dayTipWindow.openWindow()

    def getTextEditWidget(self):
        return self.tabWidget.currentWidget()

    def setupStatusBar(self):
        self.pathLabel = QLabel()
        self.cursorPosLabel = QLabel(self.env.translate("mainWindow.statusBar.cursorPosLabel") % (1,1))
        self.lexerLabel = QLabel()
        self.encodingLabel = QLabel()
        self.statusBar().addWidget(self.pathLabel)
        self.statusBar().addPermanentWidget(self.encodingLabel)
        self.statusBar().addPermanentWidget(self.lexerLabel)
        self.statusBar().addPermanentWidget(self.cursorPosLabel)

    def setupMenubar(self):
        self.menubar = self.menuBar()
        self.recentFilesMenu = QMenu(self.env.translate("mainWindow.menu.openRecent"))
        self.recentFilesMenu.setIcon(getThemeIcon(self.env,"document-open-recent"))

        self.filemenu = self.menubar.addMenu("&" + self.env.translate("mainWindow.menu.file"))
        
        new = QAction("&" + self.env.translate("mainWindow.menu.file.new"),self)
        new.setIcon(getThemeIcon(self.env,"document-new"))
        new.triggered.connect(self.newMenuBarClicked)
        new.setData(["newFile"])
        self.filemenu.addAction(new)

        self.templateMenu = QMenu(self.env.translate("mainWindow.menu.newTemplate"),self)
        self.templateMenu.setIcon(getThemeIcon(self.env,"document-new"))
        self.updateTemplateMenu()
        self.filemenu.addMenu(self.templateMenu)
        
        self.filemenu.addSeparator()

        openmenu = QAction("&" + self.env.translate("mainWindow.menu.file.open"),self)
        openmenu.setIcon(getThemeIcon(self.env,"document-open"))
        openmenu.triggered.connect(self.openMenuBarClicked)
        openmenu.setData(["openFile"])
        self.filemenu.addAction(openmenu)

        
        openDirectoryMenu = QAction(self.env.translate("mainWindow.menu.file.openDirectory"),self)
        openDirectoryMenu.setIcon(getThemeIcon(self.env,"folder-open"))
        openDirectoryMenu.triggered.connect(self.openDirectoryMenuBarClicked)
        openDirectoryMenu.setData(["directoryOpen"])
        self.filemenu.addAction(openDirectoryMenu)

        self.filemenu.addMenu(self.recentFilesMenu)

        self.filemenu.addSeparator()

        save = QAction("&" + self.env.translate("mainWindow.menu.file.save"),self)
        save.setIcon(getThemeIcon(self.env,"document-save"))
        save.triggered.connect(lambda: self.saveMenuBarClicked(self.tabWidget.currentIndex()))
        save.setData(["saveFile"])
        self.filemenu.addAction(save)

        saveAs = QAction("&" + self.env.translate("mainWindow.menu.file.saveAs"),self)
        saveAs.setIcon(getThemeIcon(self.env,"document-save-as"))
        saveAs.triggered.connect(lambda: self.saveAsMenuBarClicked(self.tabWidget.currentIndex()))
        saveAs.setData(["saveAsFile"])
        self.filemenu.addAction(saveAs)

        saveAll = QAction(self.env.translate("mainWindow.menu.file.saveAll"),self)
        saveAll.setIcon(getThemeIcon(self.env,"document-save-all"))
        saveAll.triggered.connect(self.saveAllMenuBarClicked)
        saveAll.setData(["saveAll"])
        self.filemenu.addAction(saveAll)

        self.filemenu.addSeparator()

        closeTab = QAction(self.env.translate("mainWindow.menu.file.close"),self)
        closeTab.setIcon(QIcon(os.path.join(self.env.programDir,"icons","document-close.png")))
        closeTab.triggered.connect(lambda: self.tabWidget.tabCloseClicked(self.tabWidget.currentIndex()))
        closeTab.setData(["closeTab"])
        self.filemenu.addAction(closeTab)
        
        closeAllTabsAction = QAction(self.env.translate("mainWindow.menu.file.closeAllTabs"),self)
        closeAllTabsAction.setIcon(QIcon(os.path.join(self.env.programDir,"icons","document-close-all.png")))
        closeAllTabsAction.triggered.connect(self.closeAllTabs)
        closeAllTabsAction.setData(["closeAllTabs"])
        self.filemenu.addAction(closeAllTabsAction)

        printMenuItem = QAction("&" + self.env.translate("mainWindow.menu.file.print"),self)
        printMenuItem.setIcon(getThemeIcon(self.env,"document-print"))
        printMenuItem.triggered.connect(self.printMenuBarClicked)
        printMenuItem.setData(["print"])
        self.filemenu.addAction(printMenuItem)

        exit = QAction("&" + self.env.translate("mainWindow.menu.file.exit"),self)
        exit.setIcon(getThemeIcon(self.env,"application-exit"))
        exit.triggered.connect(self.close)
        exit.setData(["exit"])
        self.filemenu.addAction(exit)
        
        self.editMenu = self.menubar.addMenu("&" + self.env.translate("mainWindow.menu.edit"))

        self.undoMenubarItem = QAction("&" + self.env.translate("mainWindow.menu.edit.undo"),self)
        self.undoMenubarItem.setIcon(getThemeIcon(self.env,"edit-undo"))
        self.undoMenubarItem.triggered.connect(lambda: self.getTextEditWidget().undo())
        self.undoMenubarItem.setData(["undo"])
        self.editMenu.addAction(self.undoMenubarItem)
        self.undoMenubarItem.setEnabled(False)

        self.redoMenubarItem = QAction("&" + self.env.translate("mainWindow.menu.edit.redo"),self)
        self.redoMenubarItem.setIcon(getThemeIcon(self.env,"edit-redo"))
        self.redoMenubarItem.triggered.connect(lambda: self.getTextEditWidget().redo())
        self.redoMenubarItem.setData(["redo"])
        self.editMenu.addAction(self.redoMenubarItem)
        self.redoMenubarItem.setEnabled(False)

        self.editMenu.addSeparator()

        self.cutMenubarItem = QAction("&" + self.env.translate("mainWindow.menu.edit.cut"),self)
        self.cutMenubarItem.setIcon(getThemeIcon(self.env,"edit-cut"))
        self.cutMenubarItem.triggered.connect(lambda: self.getTextEditWidget().cut())
        self.cutMenubarItem.setData(["cut"])
        self.editMenu.addAction(self.cutMenubarItem)
        self.cutMenubarItem.setEnabled(False)

        self.copyMenubarItem = QAction("&" + self.env.translate("mainWindow.menu.edit.copy"),self)
        self.copyMenubarItem.setIcon(getThemeIcon(self.env,"edit-copy"))
        self.copyMenubarItem.triggered.connect(lambda: self.getTextEditWidget().copy())
        self.copyMenubarItem.setData(["copy"])
        self.editMenu.addAction(self.copyMenubarItem)
        self.copyMenubarItem.setEnabled(False)

        paste = QAction("&" + self.env.translate("mainWindow.menu.edit.paste"),self)
        paste.setIcon(getThemeIcon(self.env,"edit-paste"))
        paste.triggered.connect(lambda: self.getTextEditWidget().paste())
        paste.setData(["paste"])
        self.editMenu.addAction(paste)

        self.deleteMenubarItem = QAction("&" + self.env.translate("mainWindow.menu.edit.delete"),self)
        self.deleteMenubarItem.setIcon(getThemeIcon(self.env,"edit-delete"))
        self.deleteMenubarItem.triggered.connect(lambda: self.getTextEditWidget().removeSelectedText())
        self.deleteMenubarItem.setData(["delete"])
        self.editMenu.addAction(self.deleteMenubarItem)
        self.deleteMenubarItem.setEnabled(False)

        self.editMenu.addSeparator()

        selectAll = QAction("&" + self.env.translate("mainWindow.menu.edit.selectAll"),self)
        selectAll.setIcon(getThemeIcon(self.env,"edit-select-all"))
        selectAll.triggered.connect(lambda: self.getTextEditWidget().selectAll())
        selectAll.setData(["selectAll"])
        self.editMenu.addAction(selectAll)

        self.editMenu.addSeparator()
 
        self.clipboardCopyMenu = QMenu(self.env.translate("mainWindow.menu.edit.copyClipboard"),self)
        
        copyPath = QAction(self.env.translate("mainWindow.menu.edit.copyClipboard.copyPath"),self)
        copyPath.triggered.connect(lambda: self.env.clipboard.setText(self.getTextEditWidget().getFilePath()))
        copyPath.setData(["copyPath"])
        self.clipboardCopyMenu.addAction(copyPath)

        copyDirectory = QAction(self.env.translate("mainWindow.menu.edit.copyClipboard.copyDirectory"),self)
        copyDirectory.triggered.connect(lambda: self.env.clipboard.setText(os.path.dirname(self.getTextEditWidget().getFilePath())))
        copyDirectory.setData(["copyDirectory"])
        self.clipboardCopyMenu.addAction(copyDirectory)

        copyFilename = QAction(self.env.translate("mainWindow.menu.edit.copyClipboard.copyFilename"),self)
        copyFilename.triggered.connect(lambda: self.env.clipboard.setText(os.path.basename(self.getTextEditWidget().getFilePath())))
        copyFilename.setData(["copyFilename"])
        self.clipboardCopyMenu.addAction(copyFilename)

        self.editMenu.addMenu(self.clipboardCopyMenu)

        self.convertCase = QMenu(self.env.translate("mainWindow.menu.edit.convertCase"),self)

        convertUppercase = QAction(self.env.translate("mainWindow.menu.edit.convertCase.uppercase"),self)
        convertUppercase.triggered.connect(lambda: self.getTextEditWidget().replaceSelectedText(self.getTextEditWidget().selectedText().upper()))
        convertUppercase.setData(["convertUppercase"])
        self.convertCase.addAction(convertUppercase)

        convertLowercase = QAction(self.env.translate("mainWindow.menu.edit.convertCase.lowercase"),self)
        convertLowercase.triggered.connect(lambda: self.getTextEditWidget().replaceSelectedText(self.getTextEditWidget().selectedText().lower()))
        convertLowercase.setData(["convertLowercase"])
        self.convertCase.addAction(convertLowercase)

        convertTitle = QAction(self.env.translate("mainWindow.menu.edit.convertCase.title"),self)
        convertTitle.triggered.connect(lambda: self.getTextEditWidget().replaceSelectedText(self.getTextEditWidget().selectedText().title()))
        convertTitle.setData(["convertTitle"])
        self.convertCase.addAction(convertTitle)

        convertSwap = QAction(self.env.translate("mainWindow.menu.edit.convertCase.swap"),self)
        convertSwap.triggered.connect(lambda: self.getTextEditWidget().replaceSelectedText(self.getTextEditWidget().selectedText().swapcase()))
        convertSwap.setData(["convertSwap"])
        self.convertCase.addAction(convertSwap)

        self.editMenu.addMenu(self.convertCase)

        self.eolModeMenu = QMenu(self.env.translate("mainWindow.menu.edit.eol"),self)
    
        self.eolModeWindows = QAction("Windows",self)
        self.eolModeWindows.triggered.connect(lambda: self.getTextEditWidget().changeEolMode(QsciScintilla.EolWindows))
        self.eolModeWindows.setData(["eolModeWindows"])
        self.eolModeWindows.setCheckable(True)
        self.eolModeMenu.addAction(self.eolModeWindows)

        self.eolModeUnix = QAction("Unix",self)
        self.eolModeUnix.triggered.connect(lambda: self.getTextEditWidget().changeEolMode(QsciScintilla.EolUnix))
        self.eolModeUnix.setData(["eolModeWindows"])
        self.eolModeUnix.setCheckable(True)
        self.eolModeMenu.addAction(self.eolModeUnix)

        self.eolModeMac = QAction("Mac",self)
        self.eolModeMac.triggered.connect(lambda: self.getTextEditWidget().changeEolMode(QsciScintilla.EolMac))
        self.eolModeMac.setData(["eolModeUnix"])
        self.eolModeMac.setCheckable(True)
        self.eolModeMenu.addAction(self.eolModeMac)

        self.editMenu.addMenu(self.eolModeMenu)
        self.editMenu.addSeparator()

        settings = QAction("&" + self.env.translate("mainWindow.menu.edit.settings"),self)
        settings.setIcon(getThemeIcon(self.env,"preferences-other"))
        settings.triggered.connect(lambda: self.env.settingsWindow.openWindow())
        settings.setData(["settings"])
        self.editMenu.addAction(settings)

        self.viewMenu = self.menubar.addMenu("&" + self.env.translate("mainWindow.menu.view"))

        self.zoomMenu = QMenu(self.env.translate("mainWindow.menu.view.zoom"),self)
        
        zoomIn = QAction(self.env.translate("mainWindow.menu.view.zoom.zoomIn"),self)
        zoomIn.triggered.connect(lambda: self.getTextEditWidget().zoomIn())
        zoomIn.setData(["zoomIn"])
        self.zoomMenu.addAction(zoomIn)

        zoomOut = QAction(self.env.translate("mainWindow.menu.view.zoom.zoomOut"),self)
        zoomOut.triggered.connect(lambda: self.getTextEditWidget().zoomOut())
        zoomOut.setData(["zoomOut"])
        self.zoomMenu.addAction(zoomOut)

        self.zoomMenu.addSeparator()

        zoom100 = QAction("100%",self)
        zoom100.triggered.connect(lambda: self.getTextEditWidget().zoomTo(1))
        zoom100.setData(["zoom100"])
        self.zoomMenu.addAction(zoom100)

        self.viewMenu.addMenu(self.zoomMenu)

        fullscreen = QAction(self.env.translate("mainWindow.menu.view.fullscreen"),self)
        fullscreen.triggered.connect(self.fullscreenMenuBarClicked)
        fullscreen.setData(["fullscreen"])
        fullscreen.setCheckable(True)
        self.viewMenu.addAction(fullscreen)
        
        self.toggleSidebarAction = QAction(self.env.translate("mainWindow.menu.view.sidebar"),self)
        self.toggleSidebarAction.triggered.connect(self.toggleSidebarClicked)
        self.toggleSidebarAction.setData(["toggleSidebar"])
        self.toggleSidebarAction.setCheckable(True)
        self.viewMenu.addAction(self.toggleSidebarAction)

        self.viewMenu.addSeparator()

        foldAllAction = QAction(self.env.translate("mainWindow.menu.view.foldAll"),self)
        foldAllAction.triggered.connect(lambda: self.getTextEditWidget().SendScintilla(QsciScintillaBase.SCI_FOLDALL,0))
        foldAllAction.setData(["foldAll"])
        self.viewMenu.addAction(foldAllAction)

        unfoldAllAction = QAction(self.env.translate("mainWindow.menu.view.unfoldAll"),self)
        unfoldAllAction.triggered.connect(lambda: self.getTextEditWidget().SendScintilla(QsciScintillaBase.SCI_FOLDALL,1))
        unfoldAllAction.setData(["unfoldAll"])
        self.viewMenu.addAction(unfoldAllAction)

        self.searchmenu = self.menubar.addMenu("&" + self.env.translate("mainWindow.menu.search"))

        search = QAction("&" + self.env.translate("mainWindow.menu.search.search"),self)
        search.setIcon(getThemeIcon(self.env,"edit-find"))
        search.triggered.connect(lambda: self.env.searchWindow.openWindow(self.getTextEditWidget()))
        search.setData(["find"])
        self.searchmenu.addAction(search)
        
        searchAndReplace = QAction("&" + self.env.translate("mainWindow.menu.search.searchAndReplace"),self)
        searchAndReplace.setIcon(getThemeIcon(self.env,"edit-find-replace"))
        searchAndReplace.triggered.connect(self.searchAndReplaceMenuBarClicked)
        searchAndReplace.setData(["findReplaceWindow"])
        self.searchmenu.addAction(searchAndReplace)
        
        gotoLine = QAction(self.env.translate("mainWindow.menu.search.gotoLine"),self)
        gotoLine.triggered.connect(lambda: self.env.gotoLineWindow.openWindow(self.getTextEditWidget()))
        gotoLine.setData(["gotoLine"])
        self.searchmenu.addAction(gotoLine)

        self.toolsMenu = self.menubar.addMenu("&" + self.env.translate("mainWindow.menu.tools"))

        pickColor = QAction(self.env.translate("mainWindow.menu.tools.pickColor"),self)
        pickColor.triggered.connect(self.pickColorClicked)
        pickColor.setData(["pickColor"])
        self.toolsMenu.addAction(pickColor)

        documentStatistics = QAction("&" + self.env.translate("mainWindow.menu.tools.documentStatistics"),self)
        documentStatistics.triggered.connect(lambda: self.env.documentStatistics.openWindow(self.getTextEditWidget()))
        documentStatistics.setData(["documentStatistics"])
        self.toolsMenu.addAction(documentStatistics)

        insertDateTime = QAction("&" + self.env.translate("mainWindow.menu.tools.insertDateTime"),self)
        insertDateTime.triggered.connect(lambda: self.env.dateTimeWindow.openWindow(self.getTextEditWidget()))
        insertDateTime.setData(["insertDateTime"])
        self.toolsMenu.addAction(insertDateTime)

        self.languageMenu = self.menubar.addMenu("&" + self.env.translate("mainWindow.menu.language"))

        self.updateLanguageMenu()

        self.encodingMenu = self.menubar.addMenu(self.env.translate("mainWindow.menu.encoding"))
        self.updateEncodingMenu()

        self.bookmarkMenu = self.menubar.addMenu(self.env.translate("mainWindow.menu.bookmarks"))

        addRemoveBookmarkAction = QAction(self.env.translate("mainWindow.menu.bookmarks.addRemoveBookmark"),self)
        addRemoveBookmarkAction.triggered.connect(self.addRemoveBookmark)
        addRemoveBookmarkAction.setData(["addRemoveBookmark"])
        self.bookmarkMenu.addAction(addRemoveBookmarkAction)

        nextBookmarkAction = QAction(self.env.translate("mainWindow.menu.bookmarks.nextBookmark"),self)
        nextBookmarkAction.triggered.connect(self.nextBookmark)
        nextBookmarkAction.setData(["nextBookmark"])
        self.bookmarkMenu.addAction(nextBookmarkAction)

        previousBookmarkAction = QAction(self.env.translate("mainWindow.menu.bookmarks.previousBookmark"),self)
        previousBookmarkAction.triggered.connect(self.previousBookmark)
        previousBookmarkAction.setData(["previousBookmark"])
        self.bookmarkMenu.addAction(previousBookmarkAction)

        clearBookmarksAction = QAction(self.env.translate("mainWindow.menu.bookmarks.clearBookmarks"),self)
        clearBookmarksAction.triggered.connect(self.clearBookmarks)
        clearBookmarksAction.setData(["clearBookmarks"])
        self.bookmarkMenu.addAction(clearBookmarksAction)

        self.executeMenu = self.menubar.addMenu(self.env.translate("mainWindow.menu.execute"))
        self.updateExecuteMenu()
        
        self.aboutMenu = self.menubar.addMenu("&?")

        openDataFolder = QAction(self.env.translate("mainWindow.menu.about.openDataDir"),self)
        openDataFolder.triggered.connect(lambda: openFileDefault(self.env.dataDir))
        openDataFolder.setData(["openDataFolder"])
        self.aboutMenu.addAction(openDataFolder)

        openProgramFolder = QAction(self.env.translate("mainWindow.menu.about.openProgramDir"),self)
        openProgramFolder.triggered.connect(lambda: openFileDefault(self.env.programDir))
        openProgramFolder.setData(["openProgramFolder"])
        self.aboutMenu.addAction(openProgramFolder)

        searchForUpdatesAction = QAction(self.env.translate("mainWindow.menu.about.searchForUpdates"),self)
        searchForUpdatesAction.triggered.connect(lambda: searchForUpdates(self.env,False))
        searchForUpdatesAction.setData(["searchForUpdates"])
        self.aboutMenu.addAction(searchForUpdatesAction)

        showDayTip = QAction(self.env.translate("mainWindow.menu.about.dayTip"),self)
        showDayTip.triggered.connect(lambda: self.env.dayTipWindow.openWindow())
        showDayTip.setData(["showDayTip"])
        self.aboutMenu.addAction(showDayTip)

        self.aboutMenu.addSeparator()

        about = QAction(self.env.translate("mainWindow.menu.about.about"),self)
        about.triggered.connect(lambda: self.env.aboutWindow.show())
        about.setData(["about"])
        self.aboutMenu.addAction(about)
    
        aboutQt = QAction(self.env.translate("mainWindow.menu.about.aboutQt"),self)
        aboutQt.triggered.connect(QApplication.instance().aboutQt)
        aboutQt.setData(["aboutQt"])
        self.aboutMenu.addAction(aboutQt)

        self.updateRecentFilesMenu()
        #self.getMenuActions(self.menubar)
        separator = QAction(self.env.translate("mainWindow.separator"))
        separator.setData(["separator"])
        self.env.menuActions["separator"] = separator

    def updateToolbar(self, settings):
        self.toolbar.clear()
        for i in settings.toolBar:
            if i == "separator":
                self.toolbar.addSeparator()
            else:
                if i in self.env.menuActions:
                    self.toolbar.addAction(self.env.menuActions[i])
                
    def getMenuActions(self, menu):
        for action in menu.actions():
            try:
                if isinstance(action.data()[0], str):
                    self.env.menuActions[action.data()[0]] = action
            except:
                pass
            if action.menu():
                self.getMenuActions(action.menu())

    def languageActionClicked(self):
        action = self.sender()
        if action:
            lexer = action.data()["lexer"]()
            self.getTextEditWidget().setSyntaxHighlighter(lexer,lexerList=action.data())

    def languagePlainTextClicked(self):
        editWidget = self.getTextEditWidget()
        editWidget.setLexer(None)
        editWidget.currentLexer = None
        editWidget.updateSettings(self.env.settings)
        editWidget.lexerName = self.env.translate("mainWindow.menu.language.plainText")
        editWidget.updateStatusBar()

    def updateTemplateMenu(self):
        self.templateMenu.clear()
        
        if len(self.env.templates) == 0:
            empty = QAction(self.env.translate("mainWindow.menu.newTemplate.empty"),self)
            empty.setEnabled(False)
            self.templateMenu.addAction(empty)
        else:
            for i in self.env.templates:
                templateAction = QAction(i[0],self)
                templateAction.setData([False,i[1]])
                templateAction.triggered.connect(self.openTemplate)
                self.templateMenu.addAction(templateAction)

    def openTemplate(self, sender):
        action = self.sender()
        if action:
            self.openFile(action.data()[1],template=True)
            
    def updateRecentFilesMenu(self):
        self.recentFilesMenu.clear()
        
        if len(self.env.recentFiles) == 0:
            empty = QAction(self.env.translate("mainWindow.menu.openRecent.empty"),self)
            empty.setEnabled(False)
            self.recentFilesMenu.addAction(empty)
        else:
            count = 1
            for i in self.env.recentFiles:
                fileItem = QAction(str(count) + ". " + i,self)
                fileItem.setData([False,i])
                fileItem.triggered.connect(self.openRecentFile)
                self.recentFilesMenu.addAction(fileItem)
                count += 1
            self.recentFilesMenu.addSeparator()
            clear = QAction(self.env.translate("mainWindow.menu.openRecent.clear"),self)
            clear.triggered.connect(self.clearRecentFiles)
            self.recentFilesMenu.addAction(clear)
            openAll = QAction(self.env.translate("mainWindow.menu.openRecent.openAll"),self)
            openAll.triggered.connect(self.openAllRecentFiles)
            self.recentFilesMenu.addAction(openAll)
        self.env.saveRecentFiles()
    
    def openRecentFile(self):
        action = self.sender()
        if action:
            self.openFile(action.data()[1])

    def clearRecentFiles(self):
        self.env.recentFiles = []
        self.updateRecentFilesMenu()

    def openAllRecentFiles(self):
        for i in self.env.recentFiles:
            self.openFile(i)

    def updateLanguageMenu(self):
        self.languageMenu.clear()
        alphabet = {}
        for i in self.env.lexerList:
            startLetter = i["name"][0]
            if not startLetter in alphabet:
                alphabet[startLetter] = []
            alphabet[startLetter].append(i)
        for c in ascii_uppercase:
            if c in alphabet:
                letterMenu = QMenu(c,self)
                for i in alphabet[c]:
                    languageAction = QAction(i["name"],self)
                    languageAction.setData(i)
                    languageAction.triggered.connect(self.languageActionClicked)
                    letterMenu.addAction(languageAction)
                self.languageMenu.addMenu(letterMenu)
        self.languageMenu.addSeparator()
        noneAction = QAction(self.env.translate("mainWindow.menu.language.plainText"),self)
        noneAction.triggered.connect(self.languagePlainTextClicked)
        self.languageMenu.addAction(noneAction)

    def updateEncodingMenu(self):
        self.encodingMenu.clear()
        self.env.encodingActions = []
        isoMenu = QMenu("ISO",self)
        utfMenu = QMenu("UTF",self)
        windowsMenu = QMenu("windows",self)
        self.encodingMenu.addMenu(isoMenu)
        self.encodingMenu.addMenu(utfMenu)
        self.encodingMenu.addMenu(windowsMenu)
        for i in getEncodingList():
            encodingAction = QAction(i,self)
            encodingAction.triggered.connect(self.changeEncoding)
            encodingAction.setCheckable(True)
            self.env.encodingActions.append(encodingAction)
            if i.startswith("ISO"):
                isoMenu.addAction(encodingAction)
            elif i.startswith("UTF"):
                utfMenu.addAction(encodingAction)
            elif i.startswith("windows"):
                windowsMenu.addAction(encodingAction)
            else:
                self.encodingMenu.addAction(encodingAction)

    def changeEncoding(self):
        action = self.sender()
        if action:
            self.getTextEditWidget().setUsedEncoding(action.text())        

    def updateExecuteMenu(self):
        self.executeMenu.clear()
        
        executeCommandMenu = QAction(self.env.translate("mainWindow.menu.execute.executeCommand"),self)
        executeCommandMenu.triggered.connect(lambda: self.env.executeCommandWindow.openWindow(self.getTextEditWidget()))
        executeCommandMenu.setData(["executeCommand"])
        self.executeMenu.addAction(executeCommandMenu)

        if len(self.env.commands) != 0:
            self.executeMenu.addSeparator()
            for i in self.env.commands:
                command = QAction(i[0],self)
                command.setData([False,i[1],i[2]])
                command.triggered.connect(lambda sender: executeCommand(self.sender().data()[1],self.getTextEditWidget(),self.sender().data()[2]))
                self.executeMenu.addAction(command)

        self.executeMenu.addSeparator()

        editCommands = QAction(self.env.translate("mainWindow.menu.execute.editCommands"),self)
        editCommands.triggered.connect(lambda: self.env.editCommandsWindow.openWindow())
        editCommands.setData(["editCommands"])
        self.executeMenu.addAction(editCommands)

    def openFile(self, path, template=None):
        for count, i in enumerate(self.tabWidget.tabs):
            if i[0].getFilePath() == path:
                self.tabWidget.setCurrentIndex(count)
                return
        if not os.path.isfile(path):
            return
        try:
            filehandle = open(path,"rb")
        except PermissionError:
            showMessageBox(self.env.translate("noReadPermission.title"),self.env.translate("noReadPermission.text") % path)
            return
        except Exception as e:
            print(e)
            showMessageBox(self.env.translate("unknownError.title"),self.env.translate("unknownError.text"))
            return
        fileBytes = filehandle.read()
        if self.env.settings.detectEncoding:
            encoding = chardet.detect(fileBytes)["encoding"]
            if encoding == "ascii":
                encoding = "UTF-8"
            elif encoding.startswith("utf"):
                encoding = encoding.upper()
        else:
            encoding = self.env.settings.defaultEncoding
        fileContent = fileBytes.decode(encoding,errors="replace")
        filehandle.close()
        if not self.getTextEditWidget().isNew:
            self.tabWidget.createTab(self.env.translate("mainWindow.newTabTitle"),focus=True)
        self.getTextEditWidget().setText(fileContent)
        self.getTextEditWidget().setModified(False)
        self.tabWidget.setTabText(self.tabWidget.currentIndex(),os.path.basename(path))
        self.tabWidget.tabsChanged.emit()
        if not template:
            self.getTextEditWidget().setFilePath(path)
        self.updateWindowTitle()
        if self.env.settings.detectEol:
            firstLine = fileContent.splitlines(True)[0]
            if firstLine.endswith("\r\n"):
                self.getTextEditWidget().setEolMode(QsciScintilla.EolWindows)
            elif firstLine.endswith("\n"):
                self.getTextEditWidget().setEolMode(QsciScintilla.EolUnix)
            elif firstLine.endswith("\r"):
                self.getTextEditWidget().setEolMode(QsciScintilla.EolMac)            
        self.getTextEditWidget().updateEolMenu()
        self.getTextEditWidget().setUsedEncoding(encoding)
        if not template:
            count = 0
            for i in self.env.recentFiles:
                if i == path:
                    del self.env.recentFiles[count]
                count += 1
            self.env.recentFiles.insert(0,path)
            self.env.recentFiles = self.env.recentFiles[:self.env.settings.maxRecentFiles]
            self.updateRecentFilesMenu()
        if self.env.settings.detectLanguage:
            for i in self.env.lexerList:
                for e in i["extension"]:
                    lexer = i["lexer"]()
                    self.getTextEditWidget().setSyntaxHighlighter(lexer,lexerList=i)

    def saveFile(self, tabid):
        editWidget = self.tabWidget.tabs[tabid][0]
        text = editWidget.text()
        text = text.encode(editWidget.getUsedEncoding(),errors="replace")
        try:
            filehandle = open(editWidget.getFilePath(),"wb")
        except PermissionError:
            showMessageBox(self.env.translate("noWritePermission.title"),self.env.translate("noWritePermission.text") % editWidget.getFilePath())
            return
        except Exception as e:
            print(e)
            showMessageBox(self.env.translate("unknownError.title"),self.env.translate("unknownError.text"))
            return
        filehandle.write(text)
        filehandle.close()
        editWidget.setModified(False)
        self.updateWindowTitle()
    
    def newMenuBarClicked(self):
        self.tabWidget.createTab(self.env.translate("mainWindow.newTabTitle"),focus=True)
            
    def openMenuBarClicked(self):
        path = QFileDialog.getOpenFileName(self,self.env.translate("mainWindow.openFileDialog.title"))       
        if path[0]:
            self.openFile(path[0])

    def openDirectoryMenuBarClicked(self):
        path = QFileDialog.getExistingDirectory(self,self.env.translate("mainWindow.openDirectoryDialog.title"))
        if path:
            fileList = os.listdir(path)
            for i in fileList:
                filePath = os.path.join(path,i)
                if os.path.isfile(filePath):
                    self.openFile(filePath)

    def saveMenuBarClicked(self,tabid):
        if self.getTextEditWidget().getFilePath() == "":
            self.saveAsMenuBarClicked(tabid)
        else:
            self.saveFile(tabid)

    def deleteMenuBarClicked(self):
        lastText = self.env.clipboard.text()
        self.getTextEditWidget().cut()
        self.env.clipboard.setText(lastText)

    def saveAsMenuBarClicked(self,tabid):
        path = QFileDialog.getSaveFileName(self,self.env.translate("mainWindow.saveAsDialog.title"))
        
        if path[0]:
            self.getTextEditWidget().setFilePath(path[0])
            self.saveFile(tabid)
            self.tabWidget.setTabText(tabid,os.path.basename(path[0]))
            self.tabWidget.tabsChanged.emit()
            self.updateWindowTitle()

    def saveAllMenuBarClicked(self):
        for i in range(len(self.tabWidget.tabs)):
            self.saveMenuBarClicked(i)

    def closeAllTabs(self):
        for i in range(self.tabWidget.count()-1,-1,-1):
            self.tabWidget.tabCloseClicked(i,notCloseProgram=True)
        self.tabWidget.createTab(self.env.translate("mainWindow.newTabTitle"),focus=True)

    def printMenuBarClicked(self):
        printer = QPrinter()  
        dialog  = QPrintDialog( printer);  
        dialog.setWindowTitle(self.env.translate("mainWindow.printDialog.title"));  
        if dialog.exec() == QDialog.Accepted:  
            #self.getTextEditWidget().document().print(printer);  
            #printer.printRange(self)
            document = QTextDocument()
            document.setPlainText(self.getTextEditWidget().text())
            document.print(printer)
 
    def fullscreenMenuBarClicked(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def searchAndReplaceMenuBarClicked(self):
        self.env.searchReplaceWindow.display(self.getTextEditWidget())

    def pickColorClicked(self):
        col = QColorDialog.getColor()
        if col.isValid():
            self.getTextEditWidget().insertText(col.name())

    def toggleSidebarClicked(self):
        if self.env.sidepane.enabled:
            self.env.sidepane.enabled = False
            self.env.sidepane.hide()
        else:
            self.env.sidepane.enabled = True
            self.env.sidepane.show()
        self.toggleSidebarAction.setChecked(self.env.sidepane.enabled)

    def addRemoveBookmark(self):
        editWidget = self.getTextEditWidget()
        line = editWidget.cursorPosLine
        editWidget.addRemoveBookmark(line)

    def nextBookmark(self):
        editWidget = self.getTextEditWidget()
        if len(editWidget.bookmarkList) == 0:
            return
        line = editWidget.cursorPosLine
        for i in editWidget.bookmarkList:
            if i > line:
                editWidget.setCursorPosition(i,0)
                return
        editWidget.setCursorPosition(editWidget.bookmarkList[0],0)

    def previousBookmark(self):
        editWidget = self.getTextEditWidget()
        if len(editWidget.bookmarkList) == 0:
            return
        line = editWidget.cursorPosLine
        oldBookmark = editWidget.bookmarkList[-1]
        for i in editWidget.bookmarkList:
            if i >= line:
                editWidget.setCursorPosition(oldBookmark,0)
                return
            oldBookmark = i
        #editWidget.setCursorPosition(editWidget.bookmarkList[-1],0)

    def clearBookmarks(self):
        editWidget = self.getTextEditWidget()
        for i in editWidget.bookmarkList:
            editWidget.markerDelete(i,0)
        editWidget.bookmarkList = []
          
    def updateSettings(self, settings):
        self.tabWidget.tabBar().setAutoHide(settings.hideTabBar)
        self.env.recentFiles = self.env.recentFiles[:self.env.settings.maxRecentFiles]
        self.updateRecentFilesMenu()
        self.updateToolbar(settings)
        self.setToolButtonStyle(settings.toolbarIconStyle)
        if settings.showToolbar:
            self.toolbar.show()
        else:
            self.toolbar.close()
        toolbarPositionList = [Qt.TopToolBarArea,Qt.BottomToolBarArea,Qt.LeftToolBarArea,Qt.RightToolBarArea]
        self.addToolBar(toolbarPositionList[settings.toolbarPosition],self.toolbar)
        if settings.applicationStyle == "default":
            QApplication.setStyle(QStyleFactory.create(self.env.defaultStyle))
        else:
            QApplication.setStyle(QStyleFactory.create(settings.applicationStyle))
        for key, value in self.env.menuActions.items():
            if key in settings.shortcut:
                value.setShortcut(settings.shortcut[key])
            else:
                value.setShortcut("")
        self.updateWindowTitle()

    def updateWindowTitle(self):
        if self.env.settings.windowFileTitle:
            self.setWindowTitle(self.tabWidget.tabText(self.tabWidget.currentIndex()) + " - jdTextEdit")
        else:
            self.setWindowTitle("jdTextEdit")

    def restoreSession(self):
        with open(os.path.join(self.env.dataDir,"session.json"),"r",encoding="utf-8") as f:
            data = json.load(f)
        for count, i in enumerate(data["tabs"]):
            if i["path"] == "":
                self.tabWidget.createTab(self.env.translate("mainWindow.newTabTitle"))
            else:
                self.tabWidget.createTab(os.path.basename(i["path"]))
                self.tabWidget.widget(count).setFilePath(i["path"])
            editWidget = self.tabWidget.widget(count)
            f = open(os.path.join(self.env.dataDir,"session_data",str(count)),"rb")
            text = f.read().decode(i["encoding"],errors="replace")
            editWidget.setText(text)
            f.close()
            editWidget.setModified(i["modified"])
            editWidget.setUsedEncoding(i["encoding"])
            for l in self.env.lexerList:
                s = l["lexer"]()
                if s.language() == i["language"]:                    
                    editWidget.setSyntaxHighlighter(s,lexerList=l)
            editWidget.bookmarkList = i["bookmarks"]
            for line in editWidget.bookmarkList:
                editWidget.markerAdd(line,0)
            editWidget.setCursorPosition(i["cursorPosLine"],i["cursorPosIndex"])
        self.tabWidget.setCurrentIndex(data["selectedTab"])
        os.remove(os.path.join(self.env.dataDir,"session.json"))
        shutil.rmtree(os.path.join(self.env.dataDir,"session_data"))
            
    def closeEvent(self, event):
        self.env.settings.showSidepane = self.env.sidepane.enabled
        self.env.settings.sidepaneWidget = self.env.sidepane.content.getSelectedWidget()
        self.env.settings.save(os.path.join(self.env.dataDir,"settings.json"))
        if self.env.settings.saveWindowState:
            windowState = {}
            saveWindowState(self,windowState,"MainWindow")
            saveWindowState(self.env.settingsWindow,windowState,"SettingsWindow")
            saveWindowState(self.env.dayTipWindow,windowState,"DayTipWindow")
            saveWindowState(self.env.editCommandsWindow,windowState,"EditCommandsWindow")
            saveWindowState(self.env.dateTimeWindow,windowState,"DateTimeWindow")
            with open(os.path.join(self.env.dataDir,"windowstate.json"), 'w', encoding='utf-8') as f:
                json.dump(windowState, f, ensure_ascii=False, indent=4)
        else:
            try:
                os.remove(os.path.join(self.env.dataDir,"windowstate.json"))
            except:
                pass
        if self.env.settings.saveSession:
            if not os.path.isdir(os.path.join(self.env.dataDir,"session_data")):
                os.mkdir(os.path.join(self.env.dataDir,"session_data"))
            data = {}
            data["selectedTab"] = self.tabWidget.currentIndex()
            data["tabs"] = []
            for i in range(self.tabWidget.count()):
                widget = self.tabWidget.widget(i)
                f = open(os.path.join(self.env.dataDir,"session_data",str(i)),"wb")
                f.write(widget.text().encode(widget.getUsedEncoding(),errors="replace"))
                f.close()
                if widget.currentLexer:
                    syntax = widget.currentLexer.language()
                else:
                    syntax = ""
                data["tabs"].append({"path":widget.getFilePath(),"modified":widget.isModified(),"language":syntax,"encoding":widget.getUsedEncoding(),"bookmarks":widget.bookmarkList,"cursorPosLine":widget.cursorPosLine,"cursorPosIndex":widget.cursorPosIndex})
            with open(os.path.join(self.env.dataDir,"session.json"), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            sys.exit(0)
        else:
            for i in range(self.tabWidget.count()-1,-1,-1):
                self.tabWidget.tabCloseClicked(i)
            event.ignore()

    def contextMenuEvent(self, event):
        pass              
