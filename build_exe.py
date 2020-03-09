#!/usr/bin/env python3
from cx_Freeze import setup, Executable

build_exe_options = {"includes":["jdTextEdit\plugins\pluginmanager"],"excludes": ["tkinter"]}

target = Executable(
    script="jdTextEdit.py",
    base="Win32GUI",
    targetName = "jdTextEdit.exe",
    icon="deploy\icon-windows.ico"
)

setup(
    name = "jdTextEdit",
    version = "7.1",
    description = "A powerful texteditor with a lot of features'",
    options = {"build_exe": build_exe_options},
    executables = [target]
)