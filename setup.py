import sys
import os
from cx_Freeze import setup, Executable

packages = ["queue", "idna"]  # need to explicitly include these modules :(

build_exe_options = {"packages": packages, "excludes": ["tkinter"], "build_exe": "build"}

setup(  
  name = "rainbow",
  version = "1.0.1",
  description = "Tiny module to embed ID3 metadata",
  options = {"build_exe": build_exe_options},
  executables = [Executable("rainbow.py")]
)
