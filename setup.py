import sys
import os
from cx_Freeze import setup, Executable

packages = ["queue", "idna", "fpcalc"]  # need to explicitly include these modules :(

build_exe_options = {"packages": packages, "excludes": ["tkinter"]}

setup(  name = "my prog",
    version = "0.1",
    description = "My application!",
    options = {"build_exe": build_exe_options},
    executables = [Executable("audius.py")])
