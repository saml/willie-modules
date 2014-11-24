'''
[github]
token = <github api token>
organizations = comma,separated,organization,list
'''

import sys
import os

from github import Github
from willie.module import commands

sys.path.append(os.path.dirname(__file__))
from botutils import SearchIndex

class GithubApi(object):
    def __init__(self, token, organizations):
        self.token = token
        self.organizations = organizations
        self.api = Github(token)
        self._projects_index = {}
        self._projects = []
    
    def _extend_projects(self, repos):
        i = 0
        while True:
            page = repos.get_page(i)
            if len(page) < 1:
                break
            self._projects.extend(page)
            i += 1


    def get_all_projects(self, include_user_repos=False):
        if not self._projects:
            for organization in self.organizations:
                org = self.api.get_organization(organization)
                repos = org.get_repos()
                self._extend_projects(repos)

            if include_user_repos:
                repos = self.api.get_user().get_repos()
                self._extend_projects(repos)

        return self._projects

    @property
    def projects_index(self):
        if not self._projects_index:
            projects = self.get_all_projects()
            items = ((project, project.name) for project in projects)
            self._projects_index = SearchIndex(items)
        return self._projects_index

    def find(self, *words):
        return self.projects_index.find(words)


def setup(bot):
    token = bot.config.github.token
    organizations = bot.config.github.organizations.split(',')
    bot.memory['githubx'] = GithubApi(token, organizations)

@commands('release')
def release(bot, trigger):
    api = bot.memory['githubx']
    args = trigger.group(2).split()
    project = api.find(*args)
    if not project:
        return bot.reply('Cannot find suitable project: {}'.format(' '.join(args)))
    bot.reply('Found: {}'.format(project.id))

