import io

from setuptools import setup

with io.open("requirements/app.txt") as f:
    install_requires = f.read().splitlines()

setup(install_requires=install_requires)
