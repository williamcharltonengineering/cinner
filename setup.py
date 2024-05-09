from setuptools import setup, find_packages

setup(
    name='cinner',
    version='0.0.1',
    description='cinner is a (pronounced check-in-er) is a multitool for keeping track of time-based projects.',
    author='William Charlton Engineering LLC',
    author_email='will@williamcharltonengineering.com',
    packages=find_packages(),
    install_requires=[
        # List your project dependencies here.
        # They will be installed by pip when your project is installed.
        # Example: 'requests>=2.25.1',
        "matplotlib"
    ],
    entry_points={
        # If your package has scripts or executables, you can specify them here.
        # Example:
        'console_scripts': ['cinner=cinner.__init__:main'],
    },
)