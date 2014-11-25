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

def setup(bot):
    token = bot.config.github.token
    organizations = bot.config.github.organizations.split(',')
    bot.memory['githubx'] = GithubApi(token, organizations)

@commands('release')
def release(bot, trigger):
    api = bot.memory['githubx']
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
        return bot.reply('Usage: project name[:new version]')
    
    project = api.find(*words)
    if not project:
        return bot.reply('Cannot find suitable project: {}'.format(' '.join(words)))

    tags = project.get_latest_releases()
    base = tags[0].name if tags else 'master'

    if version:
        compare_url = project.get_compare_url(base, version)
        bot.reply('Diff: {}'.format(compare_url))
    else:
        compare_url = project.get_compare_url(base)
        bot.reply('Last release of {}: {} | Diff: {}'.format(project.name, base, compare_url))
