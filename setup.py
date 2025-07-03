from setuptools import setup, find_packages

setup(
    name="comisiones-mio",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "pandas",
        "plotly",
        "openpyxl",
        "pyinstaller"
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Análisis de Chips Express",
    python_requires=">=3.8",
) 