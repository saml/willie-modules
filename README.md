# Manual

command|what
--------|-------
.lastly jenkins build name|last build
.next github project name|suggests next release version
.release github project name|creates github release with automatically suggested version
.release github project name`|`release title|creates github release with given title
.release github project name`|`release title`|`version|creates github release with given title and specific version

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
