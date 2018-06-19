from setuptools import setup

setup(
  name='aws-mfa',
  version='1.0',
  py_modules=['aws_mfa'],
  install_requires=[
    'boto3>=1.5.20',
    'click>=6.7',
    'PyYAML>=3.12'
  ],
  entry_points='''
    [console_scripts]
    aws-mfa=aws_mfa:cli
  ''',
)