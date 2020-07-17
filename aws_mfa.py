#!/bin/env python3

### https://github.com/cwells/aws-mfa

import os
import yaml
import click
import boto3
import psutil
from functools import partial
from collections import ChainMap
from datetime import datetime, timezone

program = 'aws-mfa'

###
### CachedSession
###
class CachedSession(dict):
  '''caches session data until expiry, then prompts for new MFA code.
  '''
  def __init__(self, profile, source):
    cache_file = os.path.expanduser(f'~/.aws/.{program}-{profile}.cache')
    os.umask(0o0077) # 0600
    with open(cache_file, 'a+') as cached_data:
      cached_data.seek(0)
      data = yaml.load(cached_data, Loader=yaml.FullLoader)

      if not data or datetime.utcnow().replace(tzinfo=timezone.utc) > data['Credentials']['Expiration']:
        code = click.prompt('MFA code', type=str, err=True)
        data = source(TokenCode=code)
        cached_data.seek(0)
        cached_data.write(yaml.dump(data))

    self.update(data)

###
### get_profile
###
def get_profile(ctx, profile):
  '''fetches requested profile and merges it with any specified
  base profiles.
  '''
  config_file = os.path.expanduser(f'~/.aws/{program}.yaml')
  try:
    config = yaml.load(open(config_file, 'r'), Loader=yaml.FullLoader)
  except:
    ctx.fail(f"Unable to open {config_file}, exiting.")

  profiles = [ config[profile] ]
  while True:
    try: # append the parent of the last profile to list
      profiles.append(config[profiles[-1]['inherits']])
    except KeyError:
      break
  # return the merged dictionaries
  return dict(ChainMap(*profiles))

###
### get_shell
###
def get_shell():
  '''returns name of current shell.
  '''
  return psutil.Process().parent().name()

###
### get_command_formats
###
def get_command_formats():
  '''return hash of formats keyed by shell name.
  '''
  formats = {
    'export {var}="{val}"'  : [ 'bash', 'fish', 'ksh', 'sh', 'zsh' ],
    'setenv {var} "{val}";' : [ 'csh', 'tcsh' ],
    'set ::env({var}) {val}': [ 'tclsh' ]
  }
  return { sh: cmd
    for cmd, shells in formats.items()
      for sh in shells
  }

###
### gather info needed by cli
###
shell_cmd = get_command_formats()
valid_shell = click.Choice(shell_cmd)
current_shell = get_shell()
help = {
  'profile': '[%s]' % click.style('default', fg='blue'),
  'expiry' : '[%s]' % click.style('86400', fg='blue'),
  'shell'  : '[%s]' % '|'.join([
    (sh if sh != current_shell else click.style(sh, fg='blue'))
    for sh in sorted(shell_cmd)
  ])
}

###
### cli
###
@click.command()
@click.option('--code',        '-c', type=click.STRING, metavar='<MFA code>')
@click.option('--profile',     '-p', type=click.STRING, metavar='<profile>', help=help['profile'], default='default')
@click.option('--aws_profile', '-a', type=click.STRING, metavar='<profile>', help=help['profile'])
@click.option('--expiry',      '-e', type=click.INT,    metavar='<seconds>', help=help['expiry'])
@click.option('--shell',       '-s', type=valid_shell,  metavar='<shell>',   help=help['shell'])
@click.pass_context
def cli(ctx, code, profile, aws_profile, expiry, shell):
  def pick(*items):
    '''return first truthy value from list.
    '''
    for i in items:
      if i: return i

  config  = get_profile(ctx, profile)
  aws_profile = pick(aws_profile, config.get('aws_profile'), 'default')
  session = boto3.Session(profile_name = aws_profile)
  sts     = session.client('sts')

  expiry = pick(expiry, config.get('expiry'), 86400)
  shell  = pick(shell, config.get('shell'), current_shell)
  device = f"arn:aws:iam::{config['account']}:mfa/{config['username']}"

  token = CachedSession(
    profile,
    partial(sts.get_session_token,
      DurationSeconds = expiry,
      SerialNumber    = device,
      TokenCode       = code
    )
  )

  response_code = token['ResponseMetadata']['HTTPStatusCode']
  if response_code != 200:
    ctx.fail(f"Unable to obtain token. Status code {response_code}, exiting.")

  credentials = token['Credentials']

  print('\n'.join([
    str.format(shell_cmd[shell], var=var, val=val)
    for var, val in {
      'AWS_PROFILE'          : aws_profile,
      'AWS_ACCESS_KEY_ID'    : credentials['AccessKeyId'],
      'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
      'AWS_SESSION_TOKEN'    : credentials['SessionToken']
    }.items()
  ]))

###
### main
###
if __name__ == '__main__':
  cli()
