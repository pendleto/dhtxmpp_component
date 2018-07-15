#!/bin/sh

rm -fr dist
rm -fr build
python3 setup.py build
python3 setup.py sdist
python3 setup.py bdist_egg
