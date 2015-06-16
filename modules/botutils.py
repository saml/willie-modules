import re

import github3

NON_WORD_RE = re.compile(r'\W+')
DIGITS = re.compile(r'(\d+)')

class SearchIndex(object):
    def __init__(self, items):
        '''items is [(key,content)].
        content must be string.'''
        index = {}
        for k,v in items:
            words = NON_WORD_RE.split(v)
            for word in words:
                index.setdefault(word, set()).add(k)
        self.index = index

    def find(self, words):
        '''returns key that has most number of words'''
        candidates = {}
        for word in words:
            for k in self.index.get(word, set()):
                candidates[k] = candidates.setdefault(k, 0) + 1

        for k,count in candidates.items():
            # adjust count so that longer key requires more words to match
            candidates[k] = count + (count/float(len(str(k))))
        
        result = sorted(candidates.items(), key=lambda x: x[1])
        if result:
            return result[-1][0]

def parse_version(version):
    return [int(num,10) for num in DIGITS.findall(version)]

def sort_versions(versions, get_version=None, descending=True):
    '''sorted version strings in ascending order.
    
    >>> sort_versions(['v0.0.1', '1.1.1-3', '0.3', '1', '1.1.1-2'])
    ['1.1.1-3', '1.1.1-2', '1', '0.3', 'v0.0.1']
    '''
    if get_version is None:
        get_version = lambda x: x
    max_digits = 0
    results = []

    # find max digits
    for version in versions:
        parsed = parse_version(get_version(version))
        digits = len(parsed)
        if digits > max_digits:
            max_digits = digits
        results.append((version,digits,parsed))

    # 0 pad ljust max digits
    for vesion,digits,parsed in results:
        parsed.extend([0] * (max_digits - digits))

    results.sort(key=lambda version,digits,parsed: parsed)
    if descending:
        results.reverse()
    return [version for version,_,_ in results]

def suggest_next_version(last_tag_name):
    '''increments minor version
    
    >>> suggest_next_version('1')
    '1.0.1'
    
    >>> suggest_next_version('1.2.3')
    '1.2.4'
    
    >>> suggest_next_version('v1.2.3-4')
    'v1.2.4'
    '''
    parsed = parse_version(last_tag_name)
    length = len(parsed)

    # ensure three numbers
    if length < 3:
        parsed.extend([0]*(3-length))

    # increment minor version
    parsed[2] = parsed[2] + 1

    prefix = 'v' if last_tag_name.startswith('v') else ''
    return prefix + '.'.join(str(num) for num in parsed[:3]) 


class GithubRepo(object):
    def __init__(self, repo):
        self.repo = repo

    def get_latest_release(self):
        l = list(self.repo.releases(1))
        if l:
            return l[0]

    def get_compare_url(self, base, head='master'):
        return '{}/compare/{}...{}'.format(self.repo.html_url, base, head)

    def get_release_url(self, tag_name):
        return '{}/releases/tag/{}'.format(self.repo.html_url, tag_name)

    def __getattr__(self, attrib):
        return getattr(self.repo, attrib)

class GithubApi(object):
    def __init__(self, token, organizations):
        self.token = token
        self.organizations = organizations
        self.api = github3.GitHub(token=token)
        self._projects_index = {}
        self._projects = []
    
    def get_all_projects(self):
        if not self._projects:
            for organization in self.organizations:
                org = self.api.organization(organization)
                if org:
                    self._projects.extend(org.repositories())

        return self._projects

    @property
    def projects_index(self):
        if not self._projects_index:
            projects = self.get_all_projects()
            items = ((project, project.name) for project in projects)
            self._projects_index = SearchIndex(items)
        return self._projects_index

    def find(self, *words):
        repo = self.projects_index.find(words)
        if repo:
            return GithubRepo(repo)



