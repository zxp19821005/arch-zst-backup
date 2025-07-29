from setuptools import setup, find_packages

setup(
    name="arch-zst-backup",
    version="1.0.0",
    description="Arch Linux ZST backup utility with GUI",
    author="zxp19821005",
    author_email="zxp19821005 dot 163 dot com",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.0.0',
    ],
    entry_points={
        'gui_scripts': [
            'arch-zst-backup=main:main',
        ],
    },
    python_requires='>=3.6',
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
    ],
)