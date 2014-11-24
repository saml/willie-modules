import re

NON_WORD_RE = re.compile(r'\W+')

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

