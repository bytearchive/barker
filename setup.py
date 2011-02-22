from setuptools import setup, find_packages

setup(name='clive',
      version='0.0.1',
      description='Clive is a hive mind for your clusters.',
      author='Paul Lathrop',
      author_email='paul@simplegeo.com',
      url='https://github.com/plathrop/clive',
      packages=find_packages(),
      tests_require=['coverage',
                     'nose',
                     'mock>=0.6.0'],
      test_suite="nose.collector"
      )
