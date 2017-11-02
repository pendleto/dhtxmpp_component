#!/bin/sh

python setup.py build
python setup.py sdist
python setup.py bdist_egg
