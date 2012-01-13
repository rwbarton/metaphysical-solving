from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$','puzzles.views.welcome'),

    url(r'^overview/$', 'puzzles.views.overview'),
    url(r'^overview/(\d+)/$', 'puzzles.views.overview_by'),

    url(r'^puzzle/(\d+)/$', 'puzzles.views.puzzle'),
    url(r'^puzzle/info/(\d+)/$', 'puzzles.views.puzzle_info'),
    url(r'^puzzle/spreadsheet/(\d+)/$', 'puzzles.views.puzzle_spreadsheet'),
    url(r'^puzzle/chat/(\d+)/$', 'puzzles.views.puzzle_chat'),
    url(r'^puzzle/set_status/(\d+)/$', 'puzzles.views.puzzle_set_status'),
    url(r'^puzzle/set_priority/(\d+)/$', 'puzzles.views.puzzle_set_priority'),
    url(r'^puzzle/remove_solver/(\d+)/$', 'puzzles.views.puzzle_remove_solver'),
    url(r'^puzzle/add_solver/(\d+)/$', 'puzzles.views.puzzle_add_solver'),
    url(r'^puzzle/logged_chat/(\d+)/$', 'puzzles.views.puzzle_logged_chat'),
    url(r'^puzzle/upload/(\d+)/$', 'puzzles.views.puzzle_upload'),

    url(r'^puzzle/user_location/$', 'puzzles.views.user_location'),
    url(r'^puzzle/go_to_sleep/$', 'puzzles.views.go_to_sleep'),

    url(r'^logout/$', 'puzzles.views.logout_user'),
    url(r'^logout_return/$', 'puzzles.views.logout_return'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^openid/', include('django_openid_auth.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
