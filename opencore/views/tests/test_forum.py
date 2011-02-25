import unittest

from zope.interface import Interface
from zope.interface import directlyProvides
from zope.interface import alsoProvides

from repoze.bfg.testing import cleanUp
from repoze.bfg import testing

from opencore.testing import DummyCatalog
from opencore.testing import DummyProfile
from opencore.testing import registerLayoutProvider

class TestShowForumsView(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _callFUT(self, context, request):
        from opencore.views.forum import show_forums_view
        return show_forums_view(context, request)

    def _register(self):
        d1 = 'Wednesday, January 28, 2009 08:32 AM'
        def dummy(date, flavor):
            return d1
        from opencore.utilities.interfaces import IAppDates
        testing.registerUtility(dummy, IAppDates)


    def test_it_empty(self):
        self._register()
        context = testing.DummyModel()
        context.title = 'abc'
        request = testing.DummyRequest()
        renderer = testing.registerDummyRenderer('templates/show_forums.pt')
        self._callFUT(context, request)
        self.assertEqual(len(renderer.forum_data), 0)

    def test_it_full(self):
        self._register()
        from opencore.models.interfaces import ICatalogSearch
        testing.registerAdapter(DummySearchAdapter, (Interface),
                                ICatalogSearch)
        context = testing.DummyModel()
        context['forum'] = testing.DummyModel()
        context['forum'].title = 'forum'
        context.title = 'abc'
        request = testing.DummyRequest()
        renderer = testing.registerDummyRenderer('templates/show_forums.pt')
        self._callFUT(context, request)
        self.assertEqual(len(renderer.forum_data), 1)

class TestShowForumView(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _callFUT(self, context, request):
        from opencore.views.forum import show_forum_view
        return show_forum_view(context, request)

    def _register(self):
        d1 = 'Wednesday, January 28, 2009 08:32 AM'
        def dummy(date, flavor):
            return d1
        from opencore.utilities.interfaces import IAppDates
        testing.registerUtility(dummy, IAppDates)

    def test_it(self):
        self._register()
        registerLayoutProvider()
        from opencore.models.interfaces import ICatalogSearch
        from opencore.models.interfaces import IForumsFolder
        testing.registerAdapter(DummySearchAdapter, (Interface),
                                ICatalogSearch)
        context = testing.DummyModel(title='abc')
        alsoProvides(context, IForumsFolder)
        intranets = testing.DummyModel(title='Intranets')
        intranets['forums'] = context
        request = testing.DummyRequest()
        renderer = testing.registerDummyRenderer('templates/show_forum.pt')
        self._callFUT(context, request)
        
        self.assertEqual(renderer._received.get('title'), 'abc')
        self.assertEqual(renderer._received.get('backto')['title'], 'Intranets')
      

class ShowForumTopicViewTests(unittest.TestCase):
    def setUp(self):
        cleanUp()
        testing.registerDummyRenderer('opencore.views:templates/formfields.pt')

    def tearDown(self):
        cleanUp()

    def _callFUT(self, context, request):
        from opencore.views.forum import show_forum_topic_view
        return show_forum_topic_view(context, request)

    def _register(self):
        d1 = 'Wednesday, January 28, 2009 08:32 AM'
        def dummy(date, flavor):
            return d1
        from opencore.utilities.interfaces import IAppDates
        testing.registerUtility(dummy, IAppDates)
        from opencore.models.interfaces import ITagQuery
        testing.registerAdapter(DummyTagQuery, (Interface, Interface),
                                ITagQuery)

    def test_no_security_policy(self):
        self._register()
        registerLayoutProvider()
        import datetime
        _NOW = datetime.datetime.now()
        context = testing.DummyModel()
        context.sessions = DummySessions()
        context.title = 'title'
        context['comments'] = testing.DummyModel()
        comment = testing.DummyModel()
        comment.creator = 'dummy'
        comment.created = _NOW
        comment.text = 'sometext'
        context['comments']['1'] = comment
        context['attachments'] = testing.DummyModel()
        from opencore.models.interfaces import ISite
        from opencore.models.interfaces import IForum
        directlyProvides(context, ISite)
        alsoProvides(context, IForum)
        context['profiles'] = profiles = testing.DummyModel()
        profiles['dummy'] = DummyProfile(title='Dummy Profile')
        request = testing.DummyRequest()
        request.environ['repoze.browserid'] = 1
        def dummy_byline_info(context, request):
            return context
        from opencore.views.interfaces import IBylineInfo
        testing.registerAdapter(dummy_byline_info, (Interface, Interface),
                                IBylineInfo)
        renderer = testing.registerDummyRenderer(
            'templates/show_forum_topic.pt')
        self._callFUT(context, request)
        self.assertEqual(len(renderer.comments), 1)
        c0 = renderer.comments[0]
        self.assertEqual(c0['text'], 'sometext')

        self.assertEqual(renderer.comments[0]['date'],
                         'Wednesday, January 28, 2009 08:32 AM')
        self.assertEqual(c0['author_name'], 'Dummy Profile')
        self.assertEqual(renderer.comments[0]['edit_url'],
                         'http://example.com/comments/1/edit.html')


    def test_with_security_policy(self):
        self._register()
        registerLayoutProvider()
        import datetime
        _NOW = datetime.datetime.now()
        context = testing.DummyModel(title='title')
        context.sessions = DummySessions()
        from opencore.models.interfaces import IForum
        alsoProvides(context, IForum)
        context['profiles'] = profiles = testing.DummyModel()
        profiles['dummy'] = DummyProfile()
        context['comments'] = testing.DummyModel()
        comment = testing.DummyModel(text='sometext')
        comment.creator = 'dummy'
        comment.created = _NOW
        context['comments']['1'] = comment
        context['attachments'] = testing.DummyModel()
        request = testing.DummyRequest()
        request.environ['repoze.browserid'] = 1
        def dummy_byline_info(context, request):
            return context
        from opencore.views.interfaces import IBylineInfo
        testing.registerAdapter(dummy_byline_info, (Interface, Interface),
                                IBylineInfo)
        self._register()
        testing.registerDummySecurityPolicy(permissive=False)

        renderer = testing.registerDummyRenderer(
            'templates/show_forum_topic.pt')
        self._callFUT(context, request)

        self.assertEqual(renderer.comments[0]['edit_url'], None)

    def test_comment_ordering(self):
        self._register()
        registerLayoutProvider()
        import datetime
        _NOW = datetime.datetime.now()
        _BEFORE = _NOW - datetime.timedelta(hours=1)

        context = testing.DummyModel()
        context.sessions = DummySessions()
        context.title = 'title'
        context['comments'] = testing.DummyModel()

        comment = testing.DummyModel()
        comment.creator = 'dummy'
        comment.created = _NOW
        comment.text = 'My dog has fleas.'
        context['comments']['1'] = comment

        comment2 = testing.DummyModel()
        comment2.creator = 'dummy'
        comment2.created = _BEFORE
        comment2.text = "My cat's breath smells like cat food."
        context['comments']['2'] = comment2

        context['attachments'] = testing.DummyModel()
        from opencore.models.interfaces import ISite
        from opencore.models.interfaces import IForum
        directlyProvides(context, ISite)
        alsoProvides(context, IForum)
        context['profiles'] = profiles = testing.DummyModel()
        profiles['dummy'] = DummyProfile(title='Dummy Profile')
        request = testing.DummyRequest()
        request.environ['repoze.browserid'] = 1
        def dummy_byline_info(context, request):
            return context
        from opencore.views.interfaces import IBylineInfo
        testing.registerAdapter(dummy_byline_info, (Interface, Interface),
                                IBylineInfo)
        renderer = testing.registerDummyRenderer(
            'templates/show_forum_topic.pt')
        self._callFUT(context, request)

        self.assertEqual(len(renderer.comments), 2)
        self.assertEqual(renderer.comments[0]['text'],
                         "My cat's breath smells like cat food.")
        self.assertEqual(renderer.comments[1]['text'],
                         'My dog has fleas.')



class dictall(dict):
    def getall(self, name):
        result = self.get(name)
        if result is None:
            return []
        return [result]

class DummySearchAdapter:
    def __init__(self, context):
        self.context = context

    def __call__(self, **kw):
        return 0, [], None

class DummyAdapter:
    def __init__(self, context, request):
        self.context = context
        self.request = request

class DummyTagQuery(DummyAdapter):
    tagswithcounts = []
    docid = 'ABCDEF01'

class DummySessions(dict):
    def get(self, name, default=None):
        if name not in self:
            self[name] = {}
        return self[name]

class DummyFile:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.size = 0

class DummySessions(dict):
    def get(self, name, default=None):
        if name not in self:
            self[name] = {}
        return self[name]