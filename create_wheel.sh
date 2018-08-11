#!/bin/sh

rm -fr dist
rm -fr build
python3 setup.py sdist bdist_wheel
