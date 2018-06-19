#!env python3

# Project: https://github.com/cwells/aws-mfa

import sys
import os
import string
import yaml
import click
import boto3
import psutil
from functools import partial
from datetime import datetime

program = 'aws-mfa'

class CachedConfig(dict):
  ''' caches session data until expiry, then prompts for
      new code.
  '''
  def __init__(self, ctx, profile, source):
    cache_file = os.path.expanduser(f'~/.aws/.{program}-{profile}.cache')
    os.umask(0o0077) # 0600
    with open(cache_file, 'a+') as cached_data:
      cached_data.seek(0)
      data = yaml.load(cached_data)

      if not data or datetime.utcnow() > data['Credentials']['Expiration']:
        code = click.prompt('MFA code', type=str, err=True)
        data = source(TokenCode=code)
        cached_data.seek(0)
        cached_data.write(yaml.dump(data))

    self.update(data)

def get_profile(ctx, profile):
  ''' fetches config for named profile, merges it
      with `default` profile, and returns result.
  '''
  config_file = os.path.expanduser(f'~/.aws/{program}.yaml')
  try:
    config = yaml.load(open(config_file, 'r'))
  except:
    click.echo(f"Unable to open {config_file}, exiting.", err=True)
    sys.exit(1)

  profile_config = config['default']
  profile_config.update(config[profile])

  return profile_config

def get_shell():
  ''' returns name of current shell.
  '''
  return psutil.Process().parent().as_dict(attrs=['name'])['name']

shells = [ 'sh', 'bash', 'ksh', 'csh', 'zsh', 'tcsh' ]

@click.command()
@click.option('--code',     '-c', type=str, metavar='<MFA code>')
@click.option('--profile',  '-p', type=str, metavar='<profile>', default='default')
@click.option('--expiry',   '-e', type=int, metavar='<seconds>', default=86400)
@click.option('--shell',    '-s', type=click.Choice(shells), metavar='<shell name>', default=get_shell())
@click.option('--account',  '-a', type=str, metavar='<AWS account>')
@click.option('--username', '-u', type=str, metavar='<AWS username>')
@click.pass_context
def cli(ctx, code, profile, expiry, shell, account, username):
  session = boto3.Session(profile_name=profile)
  sts = session.client('sts')
  config = get_profile(ctx, profile)
  device_arn = f"arn:aws:iam::{config['account']}:mfa/{config['username']}"

  token = CachedConfig(
    ctx, profile,
    partial(sts.get_session_token,
      DurationSeconds = expiry,
      SerialNumber    = device_arn,
      TokenCode       = code
    )
  )

  shell_template = string.Template({
    'csh' : 'setenv $var "$val"',
    'tcsh': 'setenv $var "$val"'
  }.get(shell, 'export $var="$val"'))

  if token['ResponseMetadata']['HTTPStatusCode'] == 200:
    credentials = token['Credentials']
    print('\n'.join([
      shell_template.substitute(var=var, val=val) for (var, val) in {
        'AWS_PROFILE'          : config['aws_profile'],
        'AWS_ACCESS_KEY_ID'    : credentials['AccessKeyId'],
        'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
        'AWS_SESSION_TOKEN'    : credentials['SessionToken']
      }.items()
    ]))

if __name__ == '__main__':
  cli()