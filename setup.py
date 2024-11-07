# setup.py

from setuptools import setup, find_packages

setup(
    name="ncs-cli",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["typer[all]", "requests"],
    entry_points={
        "console_scripts": [
            "ncs-cli = ncs_cli.cli:app",
        ],
    },
    author="toilaluan",
    author_email="tranthanhluan.nd@gmail.com",
    description="A CLI tool for interacting with the NCS API.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/condenses/subnet-organic",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
