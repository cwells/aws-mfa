# aws-mfa
Python script for managing multiple AWS MFA sessions.

### Requirements
Python 3.6 or later.

### Installation
```bash
python3 setup.py install --user
```

or for development mode:

```bash
python3 setup.py develop --user
```

### Configuration
> The following presumes you have a functional AWS CLI configuration. If you aren't
sure, please refer to the [official documentation][cli-getting-started].


Create `~/.aws/aws-mfa.yaml` with a `default` profile:

```yaml
---
default:
  account    : 1234567890                 # aws account id  required
  username   : phil@veridiandynamics.com  # iam username    required
  aws_profile: default                    # aws profile     optional  [default]
  expiry     : 86400                      # ttl in seconds  optional  [86400]
  shell      : bash                       # output format   optional  [auto-detect]
```
You can define as many profiles as you need. If no profile is selected
via the `--profile` option, then the `default` profile is used.

Profiles can inherit from other profiles (which in turn can inherit from
other profiles in a chain):

```yaml
default :
  username : phil@veridiandynamics.com
  expiry   : 28800

production :
  inherits : default
  account  : 111111111111

production-us :
  inherits    : production-default
  aws_profile : production-us

production-eu :
  inherits    : production-default
  aws_profile : production-eu

staging :
  inherits    : default
  account     : 222222222222
  aws_profile : staging
  expiry      : 86400
```

### Usage
In a shell, run:

```bash
$ eval $(aws-mfa)                       # will prompt for code
$ eval $(aws-mfa -c 123456 -p staging)  # specify code and profile
```

### Notes on caching
Session data is cached, so that if you run the program again before
the expiry (e.g. from another shell), it will not prompt for a code
a second time, and will instead reuse the existing session.

Cache data is stored under `~/.aws/.aws-mfa.${profile}.cache`.

Because the profile is used as part of the cache name, any number of
concurrent sessions with any number of unique profiles is supported
(in different shells, of course).


[cli-getting-started]: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

