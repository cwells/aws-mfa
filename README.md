# aws-mfa
Python script for managing AWS MFA sessions.

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
Create ~/.aws/aws-mfa.yaml with the following content:
```yaml
---
default:
  account: 1234567890
  username: phil@veridiandynamics.com
  aws_profile: production
  expiry: 86400
```

Because every profile inherits values from the `default` profile,
you need only specify the differences in additional profiles:
```yaml
staging:
  account: 3456789012
  aws_profile: staging
```

### Usage
In terminal, type:
```bash
$ eval $(aws-mfa)                       # will prompt for code
$ eval $(aws-mfa -c 123456 -p staging)  # specify code and profile
```

### Notes on caching
Session data is cached, so that if you run the program again before
the expiry has arrived, it will not prompt for the MFA code, but simply
reuse the existing session.

Cache data is stored under `~/.aws/.aws-mfa.${profile}.cache`.

Because the profile is used as part of the cache name, multiple concurrent
sessions with unique profiles are supported (in different terminals).
