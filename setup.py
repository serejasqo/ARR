from setuptools import setup, find_packages

setup(
    name="arigami_bot",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "aiogram==3.0.0b7",
        "matplotlib==3.7.1",
        "numpy==1.24.3",
        "Pillow==9.5.0"
    ],
)
