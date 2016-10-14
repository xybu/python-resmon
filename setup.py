#!/usr/bin/python3

import os
import platform

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'README.md')) as f:
        readme = f.read()
except IOError:
    readme = 'Please read README.md for more details.'


description = """
A resource monitor that records resource usage (e.g., CPU usage, RAM usage and free,
disk I/O count, NIC speed, etc.) and outputs the data in CSV format that is easy to
post-process.
"""

with open('requirements.txt', 'r') as f:
    install_requires = f.readlines()

setup(
    name='python-resmon',
    version='1.0',
    author='Xiangyu Bu',
    author_email='xybu92@live.com',
    license='MIT License',
    keywords=['resource', 'monitor', 'csv', 'process', 'usage'],
    url='https://github.com/xybu/python-resmon',
    description=description,
    long_description=readme,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: System',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring',
        'Topic :: Utilities'],
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True,
    exclude_package_data={'': ['README.*']},
    entry_points={
        'console_scripts': [
            'resmon = resmon.resmon:main',
        ]
    }
)
