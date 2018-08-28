import os
import codecs
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='lc',
    version='0.1',

    description='Beta reducer and shorthand representer for the λ-calculus',
    long_description=long_description,

    url='https://github.com/jackrosenthal/lambdacalc',

    author='Jack Rosenthal',
    author_email='jack@rosenth.al',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Education',
        'Topic :: Software Development :: Interpreters',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='lambda calculus teaching',
    scripts=['lc.py'],
    python_requires='>=3.4, <4',
    install_requires=[],

    entry_points={
        'console_scripts': [
            'lc=lc:repl',
        ],
    },
)
