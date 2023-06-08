from setuptools import setup, find_packages

setup(
    name='cubestat',
    version='0.1.1',
    author='Oleksandr Kuvshynov',
    author_email='okuvshynov@gmail.com',
    description='Horizon chart in terminal for CPU/GPU/ANE monitoring for Apple M1/M2',
    long_description='Horizon chart in terminal for CPU/GPU/ANE monitoring for Apple M1/M2',
    packages=find_packages(),
    url='https://github.com/okuvshynov/cubestat',
    entry_points={
        'console_scripts': [
            'cubestat = cubestat.cubestat:main'
        ]
    },
)