from setuptools import setup, find_packages

setup(
    name='cubestat',
    version='0.0.10',
    author='Oleksandr Kuvshynov',
    author_email='okuvshynov@gmail.com',
    description='Horizon chart in terminal for system monitoring',
    long_description='Horizon chart in terminal. Supports CPU/GPU/ANE/RAM/IO monitoring for Apple M1/M2, nVidia GPUs',
    packages=find_packages(),
    install_requires=[
        'psutil>=5.9.5',
        'pynvml; platform_system=="Linux"'
    ],
    url='https://github.com/okuvshynov/cubestat',
    entry_points={
        'console_scripts': [
            'cubestat = cubestat.cubestat:main'
        ]
    },
)
