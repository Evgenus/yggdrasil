import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()
LICENSE = open(os.path.join(here, 'LICENSE')).read()
requires = open(os.path.join(here, 'requirements.txt')).readlines()

classifiers = """
Programming Language :: Python
""".split("\n")

setup(name='yggdrasil',
      version='0.0.1',
      description='OOP abstraction over versioned graph database',
      long_description=README + '\n\n' + CHANGES,
      classifiers=classifiers,
      author='Eugene Chernyshov',
      author_email='chernyshov.eugene@gmail.com',
      url='',
      license=LICENSE,
      keywords='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="yggdrasil.tests",
      ) 