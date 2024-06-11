from setuptools import setup, find_packages

setup(
    name='rosemary',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'click',
        'python-dotenv',
    ],
    author='David Romero',
    author_email='drorganvidez@us.es',
    description="Rosemary is a CLI to be able to work on UVLHub development more easily.",
    entry_points={
        'console_scripts': [
            'rosemary=rosemary.cli:cli'
        ],
    },
)
