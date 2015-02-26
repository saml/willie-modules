'''
[github]
token = <github api token>
organizations = comma,separated,organization,list
'''

import sys
import os

from willie.module import commands

sys.path.append(os.path.dirname(__file__))
from botutils import GithubApi
import botutils

def find_latest_release(repo):
    release = repo.get_latest_release()
    current_version = release.tag_name if release else ''
    next_version = botutils.suggest_next_version(current_version) if current_version else 'v0.0.1'
    base = release.tag_name if release else 'master'
    return release,base,next_version

def setup(bot):
    token = bot.config.github.token
    organizations = bot.config.github.organizations.split(',')
    bot.memory['githubx'] = GithubApi(token, organizations)
    
@commands('next')
def nextver(bot, trigger):
    argline = trigger.group(2)
    if not argline:
        return bot.reply('Usage: project name')

    args = argline.split(' ')
    api = bot.memory['githubx']
    repo = api.find(*args)
    if not repo:
        return bot.reply('Cannot find suitable project: {}'.format(argline))
    
    release,base,next_version = find_latest_release(repo)
    bot.reply('Next version: {} | Current version: {}'.format(next_version, base))


@commands('release')
def release(bot, trigger):
    argline = trigger.group(2)
    args = argline.split(':') if argline else []
    argc = len(args)
    words = []
    version = None
    if argc == 2:
        words,version = args
        words = words.split(' ')
    elif argc == 1:
        words = args[0].split(' ')
    else:
        bot.reply('Usage: project name[:new version]')
        return

    api = bot.memory['githubx']
    repo = api.find(*words)
    if not repo:
        return bot.reply('Cannot find suitable project: {}'.format(' '.join(words)))

    release,base,suggested_version = find_latest_release(repo)
    if version is None:
        version = suggested_version

    compare_url = repo.get_compare_url(base, version)
    new_release = repo.create_release(version, body=compare_url)
    bot.reply('New release created: {}'.format(new_release.html_url))

