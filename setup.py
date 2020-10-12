import os.path
from setuptools import setup

root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')

setup(
    name='PyNBT',
    version='3.1.0',
    description='Tiny, liberally-licensed NBT library (Minecraft).',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='https://github.com/TkTech/PyNBT',
    keywords=['minecraft', 'nbt'],
    py_modules=['pynbt'],
    install_requires=[
        'mutf8>=1.0.2'
    ],
    extras_require={
        'test': ['pytest']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License'
    ]
)
