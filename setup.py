from setuptools import setup, find_packages

setup(
    name='pytest-typed-schema-shot',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'click',
        'genson',
        'jsonschema',
        'pytest',
    ]
    author='Miskler',
    description='Pytest plugin for automatic JSON Schema generation and validation from examples',
    long_description=open('README.md', encoding="utf-8").read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Open-Inflation/pytest-typed-schema-shot',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Topic :: Utilities',
    ],
    python_requires='>=3.10',
)
