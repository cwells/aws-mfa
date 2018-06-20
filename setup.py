from setuptools import setup

setup(
  name       = 'aws-mfa',
  version    = '1.6',
  py_modules = ['aws_mfa'],

  install_requires = open('requirements.txt').readlines(),

  entry_points = '''
    [console_scripts]
    aws-mfa=aws_mfa:cli
  '''
)