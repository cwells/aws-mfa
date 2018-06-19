from setuptools import setup

setup(
  name='aws-mfa',
  version='1.0',
  py_modules=['aws-mfa'],
  install_requires=[
    'boto3>=1.5.20',
    'click>=6.7',
    'PyYAML>=3.12'
  ],
  entry_points='''
    [console_scripts]
    yourscript=aws-mfa:cli
  ''',
)