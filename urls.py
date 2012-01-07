from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'solving.views.home', name='home'),
    url(r'^overview/$', 'puzzles.views.overview'),
    url(r'^overview/(\d+)/$', 'puzzles.views.overview_by'),

    url(r'^puzzle/(\d+)/$', 'puzzles.views.puzzle'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^','puzzles.views.welcome'),
)
