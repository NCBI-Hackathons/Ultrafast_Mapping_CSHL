from setuptools import setup
import os
import sys

if sys.version_info < (3, 3):
    sys.stdout.write("At least Python 3.3 is required.\n")
    sys.exit(1)

setup(
    name='pipeline',
    version='0.1',
    description='Our UltraFast (tm) pipeline for calling expressed variants',
    url='https://github.com/NCBI-Hackathons/Ultrafast_Mapping_CSHL',
    author='Andrew Fant, Ben Busby, John Didion, Morgan Taschuk, Upendra K?',
    author_email='john.didion@nih.gov',
    license='MIT',
    packages=['pipeline'],
    scripts = ['scripts/align.py'],
    package_dir={'pipeline': 'src'},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ]
)
