"""
    A repoze.who plugin to support api-key requests, where
    a small number of keys are contained in the 

"""
from urlparse import parse_qs

class APIKeyPlugin(object):

    def __init__(self, key_name, keys='', user_name=''):
        self.key_name = key_name.strip()
        self.valid_keys = [v.strip() for v in keys.split(',')]
        self.user_name = user_name.strip()

    def identify(self, environ):
        this_key = self._extract_key(environ)
        if this_key and this_key in self.valid_keys:
            return {'repoze.who.userid' : self.user_name}
        else:
            return None

    def forget(self, environ, identity):
        return None

    def remember(self, environ, identity):
        return None
    
    def _extract_key(self, environ):
        try:
            return parse_qs(environ['QUERY_STRING'])[self.key_name][0]
        except Exception:
            return None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, id(self))

def make_plugin(key_name=None, keys='', user_name=''):
    return APIKeyPlugin(key_name, keys, user_name)
