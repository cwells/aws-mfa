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
Create `~/.aws/aws-mfa.yaml` with the following information:
```yaml
---
default:
  account: 1234567890                  # required
  username: phil@veridiandynamics.com  # required
  aws_profile: production              # optional [default]
  expiry: 3600                         # optional [86400]
  shell: bash                          # optional [auto-detect]
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
$ eval $( aws-mfa )                       # will prompt for code
$ eval $( aws-mfa -c 123456 -p staging )  # specify code and profile
```

### Notes on caching
Session data is cached, so that if you run the program again before
the expiry (e.g. from another shell), it will not prompt for a code 
a second time, and will instead reuse the existing session.

Cache data is stored under `~/.aws/.aws-mfa.${profile}.cache`.

Because the profile is used as part of the cache name, multiple concurrent
sessions with unique profiles are supported (in different shells, of course).
