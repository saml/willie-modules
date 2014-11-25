'''
add this to ~/.willie/default.cfg

[jenkins]
url = http://jenkins.example.com
user = your-jenkins-username
key = your-jenkins-api-key
'''

import re
import operator
import os
import sys
import datetime

import requests
from willie.module import commands

sys.path.append(os.path.dirname(__file__))
from botutils import SearchIndex

NON_WORD_RE = re.compile(r'\W+')

class Jenkins(object):
    def __init__(self, url, auth):
        self.url = url
        self.auth = auth
        self._jobs_index = {}

    @property
    def jobs_index(self):
        if not self._jobs_index:
            jobs = self.get_all_jobs()
            items = ((job['url'],job['name']) for job in jobs)
            self._jobs_index = SearchIndex(items)
        return self._jobs_index


    def get(self, url, auth=None):
        resp = requests.get(url, auth=auth or self.auth)
        if resp.status_code == 200:
            return resp.json()
        return None

    def post(self, url, data=None, auth=None):
        return requests.post(url, auth=auth or self.auth, data=data)

    def get_all_jobs(self):
        url = self.url+'/api/json'
        print('Getting all jobs: {}'.format(url))
        return requests.get(url, auth=self.auth).json()['jobs']

    def find_job(self, *args):
        return self.jobs_index.find(args)


    def build(self, build_name):
        job = self.find_job(build_name)
        url = job['url']+'build'
        resp = self.post(url)


regex_tag = re.compile(r"^v\d+")
regex_remoteurl = re.compile(r'git@github\.com:(.+)\.git$')

def get_github_link(branch_name, project_home_url):
    if regex_tag.search(branch_name):
        #it's a tag
        return project_home_url+'/releases/tag/'+branch_name
    return project_home_url+'/tree/'+branch_name

def parse_jenkins_resp(resp):
    started_by_id = None
    started_by = None
    built_sha1 = None
    built_branch_name = None
    project_home_url = None

    for action in resp['actions']:
        if 'causes' in action:
            for cause in action['causes']:
                if 'userId' in cause and 'userName' in cause and 'shortDescription' in cause and cause['shortDescription'].startswith('Started by user '):
                    started_by_id = cause['userId']
                    started_by = cause['userName']
        if 'lastBuiltRevision' in action:
            lastBuiltRevision = action['lastBuiltRevision']
            built_sha1 = lastBuiltRevision['SHA1']
            branch = lastBuiltRevision.get('branch', [{}])[0]
            built_branch_name = branch['name']
        if 'remoteUrls' in action:
            for remoteUrl in action['remoteUrls']:
                m = regex_remoteurl.match(remoteUrl)
                if m:
                    project_home_url = 'https://github.com/'+m.group(1)


    return (started_by_id, started_by, built_sha1, built_branch_name, project_home_url)

def setup(bot):
    auth = (bot.config.jenkins.user, bot.config.jenkins.key)
    bot.memory['jenkins'] = Jenkins(bot.config.jenkins.url, auth)

@commands('lastly')
def lastly(bot, trigger):
    argline = trigger.group(2) or ''
    args = argline.split()
    if not args:
        return bot.reply('need jenkins project name')
    jenkinsapi = bot.memory['jenkins']
    job = jenkinsapi.find_job(*args)
    if not job:
        return bot.reply('Cannot find suitable jenkins job: {}'.format(argline))
    url = os.path.join(job, 'lastBuild/api/json')
    resp = jenkinsapi.get(url)
    if not resp:
        return bot.reply('No build on: '+url)
    started_by_id,started_by,built_sha1,built_branch_name,project_home_url = parse_jenkins_resp(resp)
    try:
        github_link = get_github_link(built_branch_name, project_home_url)
    except:
        github_link = None
    bot.reply('%s lastly started by "%s" (%s) on %s (%s) => %s | %s (%s) | %s' % (
            resp['fullDisplayName'],
            started_by, started_by_id,
            datetime.datetime.fromtimestamp(resp['timestamp']/1000).isoformat(),
            resp['url'],
            resp.get('result', 'NO RESULT'),
            built_branch_name, github_link, built_sha1))

