import sys
from cx_Freeze import setup, Executable

setup(
        name="RCFileChekcer",
        version="1.0",
        description = "RCFileChekcer",
        author = "pyj0827@midasit.com",
        executables = [Executable("Resource_Checker.py")])