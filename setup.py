from setuptools import setup, find_packages

setup(
    name='presis',
    version='0.0.1',
    description='presis is a (pronounced check-in-er) is a multitool for keeping track of time-based projects.',
    author='William Charlton Engineering LLC',
    author_email='will@williamcharltonengineering.com',
    packages=find_packages(),
    install_requires=[
        # List your project dependencies here.
        # They will be installed by pip when your project is installed.
        # Example: 'requests>=2.25.1',
        "matplotlib",
        "werkzeug",
        "kivy",
        "redis",
        "jwt",
    ],
    entry_points={
        # If your package has scripts or executables, you can specify them here.
        # Example:
        'console_scripts': ['presis=presis.__init__:main'],
    },
)