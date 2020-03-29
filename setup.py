#!/usr/bin/env python

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

install_deps = [
    'Pillow',
    'tqdm',
],
test_deps = [
    "coveralls>=1.4.0",
    "pytest>=5.0.0",
    "pytest-cov>=2.6.1",
]

setup(
    name="factorio-leaflet-maps",
    version="0.1.0",
    author="Mark Vander Stel",
    author_email="mvndrstl@gmail.com",
    description="Convert a TAR file or directory of Factorio screenshots into Leaflet map tiles.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Rycieos/factorio-leaflet-maps",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_deps,
    tests_require=test_deps,
    extras_require={"test": test_deps},
    zip_safe=False,
    python_requires=">=3.5",
    entry_points={
        "console_scripts": [
            "factoriomap = factoriomap:main"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
