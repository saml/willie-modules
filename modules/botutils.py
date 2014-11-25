import re

from github import Github

NON_WORD_RE = re.compile(r'\W+')
DIGITS = re.compile(r'(\d+)')

class SearchIndex(object):
    def __init__(self, items):
        '''items is [(key,content)].
        both key and content are string.'''
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
        result = sorted(candidates.items(), key=lambda (k,count): count)
        if result:
            return result[-1][0]

def parse_version(version):
    return [int(num,10) for num in DIGITS.findall(version)]

def sort_versions(versions, get_version=None, descending=True):
    '''sorted version strings in ascending order.
    
    >>> sort_versions(['v0.0.1', '1.1.1-3', '0.3', '1', '1.1.1-2'])
    ['v0.0.1', '0.3', '1', '1.1.1-2', '1.1.1-3']
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

    for vesion,digits,parsed in results:
        parsed.extend([0] * (max_digits - digits))

    results.sort(key=lambda (version,digits,parsed): parsed)
    if descending:
        results.reverse()
    return [version for version,_,_ in results]


def get_all(paginated_list):
    result = []
    i = 0
    while True:
        page = paginated_list.get_page(i)
        if len(page) < 1:
            break
        result.extend(page)
        i += 1
    return result

class GithubRepo(object):
    def __init__(self, repo):
        self.repo = repo

    def get_latest_releases(self, limit=3):
        tags = self.repo.get_tags().get_page(0)
        if tags:
            return sort_versions(tags, lambda tag: tag.name)[:limit]
        return []

    def get_compare_url(self, base, head='master'):
        return '{}/compare/{}...{}'.format(self.repo.html_url, base, head)

    def __getattr__(self, attrib):
        return getattr(self.repo, attrib)

class GithubApi(object):
    def __init__(self, token, organizations):
        self.token = token
        self.organizations = organizations
        self.api = Github(token)
        self._projects_index = {}
        self._projects = []
    
    def get_all_projects(self, include_user_repos=False):
        if not self._projects:
            for organization in self.organizations:
                org = self.api.get_organization(organization)
                repos = org.get_repos()
                self._projects.extend(get_all(repos))

            if include_user_repos:
                repos = self.api.get_user().get_repos()
                self._projects.extend(get_all(repos))

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



