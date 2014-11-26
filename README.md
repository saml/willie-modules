# Quickstart

Install [willie](http://willie.dftba.net/) and run it.
Edit `~/.willie/default.cfg`:

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
