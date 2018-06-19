#!/bin/env python3

#
# Create ~/.aws/aws-mfa.yaml with the following settings:
#
# ---
# default:
#   account: 1234567890
#   username: phil@veridiandynamics.com
#   aws_profile: production
#   expiry: 86400
#
# Every profile inherits values from the `default` profile, and as
# such, you need only specify the differences in additional profiles:
#
# staging:
#   account: 3456789012
#   aws_profile: staging
#
# Usage (in terminal):
#
#   $ eval $(aws-mfa)                       # will prompt for code
#   $ eval $(aws-mfa -c 123456 -p staging)  # specify code and profile
#

import sys
import os
import yaml
import click
import boto3
from functools import partial
from datetime import datetime

class CachedConfig(dict):
  def __init__(self, ctx, profile, source):
    program = os.path.splitext(ctx.command_path)[0]
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
  program = os.path.splitext(ctx.command_path)[0]
  config_file = os.path.expanduser(f'~/.aws/{program}.yaml')
  try:
    config = yaml.load(open(config_file, 'r'))
  except:
    click.echo(f"Unable to open configuration file {config_file}, exiting.", err=True)
    sys.exit(1)

  profile_config = config['default']
  profile_config.update(config[profile])

  return profile_config

@click.command()
@click.option('--code',     '-c', type=str, metavar='<MFA code>')
@click.option('--profile',  '-p', type=str, metavar='<profile>')
@click.option('--expiry',   '-e', type=int, metavar='<seconds>')
@click.option('--account',  '-a', type=str, metavar='<AWS account>')
@click.option('--username', '-u', type=str, metavar='<AWS username>')
@click.pass_context
def cli(ctx, code, profile, expiry, account, username):
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

  if token['ResponseMetadata']['HTTPStatusCode'] == 200:
    credentials = token['Credentials']
    print('\n'.join([
      f'export {k}="{v}"' for (k, v) in {
        'AWS_PROFILE':           config['aws_profile'],
        'AWS_ACCESS_KEY_ID':     credentials['AccessKeyId'],
        'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
        'AWS_SESSION_TOKEN':     credentials['SessionToken']
      }.items()
    ]))

if __name__ == '__main__':
  cli(default_map={
    'profile': 'default',
    'expiry':  86400
  })
