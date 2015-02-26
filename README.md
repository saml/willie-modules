# Usage

Given github project `foobar` and jenkins build `foobar-prd`:


```sh
# Gives latest jenkins build info.
.lastly foobar prd

# Suggests next release version.
.next foobar

# Creates github release with suggested version.
.release foobar

# Creates github release with suggested version. Release title is also specified.
.release foobar|fixing some bug

# Creates github release with specified version and title.
. release foobar|fixing some bug|v1.0.0
```

# Quickstart

Install [willie](http://willie.dftba.net/) and run it to generate `~/.willie/default.cfg`.
Edit `default.cfg`:

```
[core]
...
extra = /path/to/willie-modules.git/modules,/home/you/.willie/modules

[jenkins]
url = https://your.jenkins
user = your-user
key = jenkins-api-key

[github]
token = github-app-token
organizations = your-organization1,your-organization2
```

And, install requirements and run:

```
pip install -r requirements.txt
willie
```

You may use virtualenv.
