import os
import os.path
import re
import codecs

from setuptools import setup, find_packages

NAME = "yggdrasil"
DESCRIPTION = "OOP abstraction over versioned graph database"

CLASSIFIERS = """
Programming Language :: Python
""".strip().split("\n")

AUTHOR = "Eugene Chernyshov"
EMAIL = "chernyshov.eugene@gmail.com"
URL = "https://github.com/Evgenus/yggdrasil"
KEYWORDS = ""

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, NAME, '__init__.py'), 'r') as fp:
    try:
        VERSION = re.findall(r"^__version__ = '([^']+)'$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()
LICENSE = open(os.path.join(here, 'LICENSE')).read()
TODO = open(os.path.join(here, 'TODO')).read()
requires = open(os.path.join(here, 'requirements.txt')).readlines()

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=README + '\n\n' + CHANGES + '\n\n' + TODO,
      classifiers=CLASSIFIERS,
      author=AUTHOR,
      author_email=EMAIL,
      url=URL,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite=NAME+".tests",
      )  