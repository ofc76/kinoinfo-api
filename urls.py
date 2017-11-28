# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from base.feeds import FilmsFeed, ArticlesFeed, ReleasesFeed

admin.autodiscover()
dajaxice_autodiscover()

urlpatterns = patterns('',

    # search
    (r'^search/', include('base.urls')),
    
    
    # api
    (r'^api/', include('api.urls')),
    
    # dajax
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    
    # сеансы
    url(r'^schedule/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/(?P<cinema>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/(?P<cinema>\w+)/(?P<id>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    
    
    
    (r'^i18n/', include('django.conf.urls.i18n')),
    
)
 
if settings.DEBUG:
    urlpatterns += patterns('',
       url(r'^' + settings.MEDIA_URL.lstrip('/') \
               + '(?P<path>.*)$', 'django.views.static.serve',
           {
                'document_root': settings.MEDIA_ROOT,
           }),
    )
    urlpatterns += staticfiles_urlpatterns()
