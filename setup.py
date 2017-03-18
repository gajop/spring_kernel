# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

PKGNAME = 'spring_kernel'
pkg = __import__( PKGNAME )

setup(
    name=PKGNAME,

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='1.0',

    description='Jupyter kernel for SpringRTS',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/gajop/spring-kernel',

    # Author details
    author='gajop',
    author_email='gajopetrovic@gmail.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Framework :: IPython',
        'Development Status :: 4 - Beta',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='springrts jupyter ipython',

    entry_points = { 'console_scripts': [
        'jupyter-springrtskernel = spring_kernel.__main__:main',
    ]},

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    #packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    packages=[PKGNAME],

    package_data = {
        PKGNAME : [ 'resources/logo-*x*.png', 'kernel_config.json' ] 
    },

    install_requires=[ "setuptools",
                   "ipykernel >= 4.0",
                   "jupyter-client >= 4.0"],
)
