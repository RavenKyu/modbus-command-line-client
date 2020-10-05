from setuptools import setup, find_packages

__version__ = '0.3.0'

LONG_DESCRIPTION = open("README.md", "r", encoding="utf-8").read()

setup(
    name="modbusclc",
    version=__version__,
    author="Duk Kyu Lim",
    author_email="hong18s@gmail.com",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    description='Modbus Command Line Client',
    url="https://github.com/RavenKyu/modbus-command-line-client",
    license="MIT",
    keywords=["cli", "modbus"],
    install_requires=[
        'cliparse',
        'pymodbus',
        'PyYaml'
    ],
    packages=find_packages(
        exclude=['dummy-modbus-server', 'dummy-modubs-server.*',
                 'tests', 'tests.*']),
    package_data={},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    zip_safe=False,
)
