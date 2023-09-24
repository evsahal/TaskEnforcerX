import sys
import os
from cx_Freeze import setup, Executable

# ADD FILES
files = ['icon.ico','images/','Tesseract-OCR/','platform-tools/','main.db']

# TARGET
target = Executable(
    script="main.py",
    base="Win32GUI",
    icon="icon.ico"
)

# SETUP CX FREEZE
setup(
    name = "TaskEnforcerX",
    version = "1.0.0",
    description = "Made for Evony Mobile",
    author = "MwoNuZzz",
    options = {'build_exe' : {'include_files' : files}},
    executables = [target]
    
)

#venv\Scripts\activate

#python setup.py build