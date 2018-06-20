#!env python3

# Project: https://github.com/cwells/aws-mfa

import os
import yaml
import click
import boto3
import psutil
from functools import partial
from datetime import datetime

program = 'aws-mfa'

class CachedSession(dict):
  '''caches session data until expiry, then prompts for new MFA code.
  '''
  def __init__(self, profile, source):
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
  '''fetches config for named profile, merges it with `default` profile, and returns result.
  '''
  config_file = os.path.expanduser(f'~/.aws/{program}.yaml')
  try:
    config = yaml.load(open(config_file, 'r'))
  except:
    ctx.fail(f"Unable to open {config_file}, exiting.")

  profile_config = config['default']
  profile_config.update(config[profile])

  return profile_config


def get_shell():
  '''returns name of current shell.
  '''
  return psutil.Process().parent().name()


shell_templates = {
  'export': 'export {var}="{val}"',
  'setenv': 'setenv {var} "{val}"'
}

shells = {
  'bash': 'export',
  'csh' : 'setenv',
  'ksh' : 'export',
  'sh'  : 'export',
  'tcsh': 'setenv',
  'zsh' : 'export'
}

shell = click.Choice(shells)
current_shell = get_shell()
help = {
  'profile': '[%s]' % click.style('default', fg='blue'),
  'expiry' : '[%s]' % click.style('86400', fg='blue'),
  'shell'  : '[%s]' % '|'.join([
    (sh if sh != current_shell else click.style(sh, fg='blue'))
    for sh in shells
  ])
}

@click.command()
@click.option('--code',    '-c', type=str,                          metavar='<MFA code>')
@click.option('--profile', '-p', type=str,   default='default',     metavar='<profile>', help=help['profile'])
@click.option('--expiry',  '-e', type=int,   default=86400,         metavar='<seconds>', help=help['expiry'])
@click.option('--shell',   '-s', type=shell, default=current_shell, metavar='<shell>',   help=help['shell'])
@click.pass_context
def cli(ctx, code, profile, expiry, shell):
  session = boto3.Session(profile_name=profile)
  sts = session.client('sts')

  config = get_profile(ctx, profile)
  device_arn = f"arn:aws:iam::{config['account']}:mfa/{config['username']}"

  token = CachedSession(
    profile,
    partial(sts.get_session_token,
      DurationSeconds = expiry,
      SerialNumber    = device_arn,
      TokenCode       = code
    )
  )

  if token['ResponseMetadata']['HTTPStatusCode'] != 200:
    ctx.fail(
      f"Unable to obtain token. HTTP error code"
      f" {token['ResponseMetadata']['HTTPStatusCode']}, exiting."
    )

  credentials = token['Credentials']
  template = shell_templates[shells[shell]]

  print('\n'.join([
    str.format(template, var=var, val=val)
    for var, val in {
      'AWS_PROFILE'          : config['aws_profile'],
      'AWS_ACCESS_KEY_ID'    : credentials['AccessKeyId'],
      'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
      'AWS_SESSION_TOKEN'    : credentials['SessionToken']
    }.items()
  ]))


if __name__ == '__main__':
  cli()