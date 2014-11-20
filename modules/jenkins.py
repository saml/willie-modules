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

NON_WORD_RE = re.compile(r'\W+')

class Jenkins(object):
    def __init__(self, url, auth):
        self.url = url
        self.auth = auth

    def get(self, url, auth=None):
        resp = requests.get(url, auth=auth or self.auth)
        if resp.status_code == 200:
            return resp.json()
        return None

    def post(self, url, data=None, auth=None):
        return requests.post(url, auth=auth or self.auth, data=data)

    def get_all_jobs(self):
        url = self.url+'/api/json'
        return requests.get(url, auth=self.auth).json()['jobs']

    def update_jobs_with_tanimoto(self, jobs, words, letters):
        for job in jobs:
            score_words = tanimoto(words, bag_of_words(job['name']))
            score_letters = tanimoto(letters, bag_of_letters(job['name']))
            job['tanimoto'] = (score_words*0.0) + (score_letters*1.0)
        return jobs

    def update_jobs_with_similarity_score(self, jobs, user_input):
        words = bag_of_words(user_input)
        for job in jobs:
            job['similarityscore'] = similarity_score_of(user_input, job['name']) + tanimoto(words, bag_of_words(job['name']))
        return jobs

    def find_job_using_tanimoto(self, *args):
        all_jobs = self.get_all_jobs()
        user_input = '-'.join(args)
        words = bag_of_words(user_input)
        letters = bag_of_letters(user_input)
        self.update_jobs_with_tanimoto(all_jobs, words, letters)
        return sorted(all_jobs, key=operator.itemgetter('tanimoto'), reverse=True)[0]
    
    def find_job(self, *args):
        all_jobs = self.get_all_jobs()
        user_input = '-'.join(args)
        self.update_jobs_with_similarity_score(all_jobs, user_input)
        return sorted(all_jobs, key=operator.itemgetter('similarityscore'), reverse=True)[0]

    def find_jobs(self, line, limit=4):
        all_jobs = self.get_all_jobs()
        self.update_jobs_with_similarity_score(all_jobs, line)
        return sorted(all_jobs, key=operator.itemgetter('similarityscore'), reverse=True)[:limit]


    def build(self, build_name):
        job = self.find_job(build_name)
        url = job['url']+'build'
        resp = self.post(url)


def normalize_str(x):
    return NON_WORD_RE.sub('', x.lower())

def similarity_score_of(a, b):
    a = normalize_str(a)
    b = normalize_str(b)
    score = 0
    for i,x in enumerate(b):
        j = a.find(b[i])
        if j != -1:
            a = a[j+1:]
            score += 1
    return score



def bag_of_words(sentence):
    return set(NON_WORD_RE.sub(' ', sentence.lower()).split())

def bag_of_letters(sentence):
    return set(NON_WORD_RE.sub('', sentence.lower()))

def tanimoto(a, b):
    return len(a.intersection(b)) * 1.0/len(a.union(b))



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
    input_line = trigger.group(2).split()
    if not input_line:
        return bot.reply('need jenkins project name')
    jenkinsapi = bot.memory['jenkins']
    job = jenkinsapi.find_job(*input_line)
    url = os.path.join(job['url'], 'lastBuild/api/json')
    resp = jenkinsapi.get(url)
    if not resp:
        return bot.reply('No build on: '+url)
    started_by_id,started_by,built_sha1,built_branch_name,project_home_url = parse_jenkins_resp(resp)
    try:
        github_link = get_github_link(built_branch_name, project_home_url)
    except:
        github_link = None
    bot.reply('%s build lastly started by "%s" (%s) on %s (%s) => %s | %s (%s) | %s' % (
            job['name'],
            started_by, started_by_id,
            datetime.datetime.fromtimestamp(resp['timestamp']/1000).isoformat(),
            resp['url'],
            resp.get('result', 'NO RESULT'),
            built_branch_name, github_link, built_sha1))

@commands('jf')
def jenkins_find(bot, trigger):
    input_line = trigger.group(2).split()
    if not input_line:
        return bot.reply('Usage: .jf jenkins project name to search')
    jenkinsapi = bot.memory['jenkins']
    jobs = jenkinsapi.find_jobs(input_line, 4)
    return bot.reply(' | '.join(('%s (%.1f)' % (x['name'], x['similarityscore']) for x in jobs)))

