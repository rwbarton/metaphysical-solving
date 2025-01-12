from django.urls import re_path, include, path
from django.views.generic.base import RedirectView
from puzzles import views
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    re_path(r'^$', views.welcome),

    re_path(r'^profile_photo/(\d+)$', views.profile_photo, name='puzzles.views.profile_photo_with_id'),
    re_path(r'^profile_photo', views.profile_photo, name='puzzles.views.profile_photo'),

    re_path(r'^api_overview', views.api_overview, name="puzzles.views.api_overview"),
    re_path(r'^api_log_a_view/(\d+)$', views.api_log_a_view, name="puzzles.views.api_log_a_view"),
    re_path(r'^api_motd', views.api_motd, name="puzzles.views.api_motd"),
    re_path(r'^api_puzzle/(\d+)$', views.api_puzzle, name='puzzles.views.api_puzzle'),
    re_path(r'^api_puzzle_history/(\d+)$', views.api_puzzle_history, name='puzzles.views.api_puzzle_history'),
    re_path(r'^api_update_puzzle/(\d+)$', views.api_update_puzzle, name='puzzles.views.api_update_puzzle'),

    re_path(r'^overview/$', views.overview, name='puzzles.views.overview'),
    re_path(r'^overview/(\d+)/$',  views.overview_by, name='puzzles.views.overview_by'),
    re_path(r'^whowhat/$', views.who_what, name='puzzles.views.who_what'),
    re_path(r'^puzzle/(\d+)/$',  views.puzzle, name='puzzles.views.puzzle'),
    #re_path(r'^puzzle_new/(\d+)/$',  views.puzzle_new, name='puzzles.views.puzzle_new'),
    re_path(r'^puzzle_bottom/(\d+)/$',  views.puzzle_bottom, name='puzzles.views.puzzle_bottom'),
    #re_path(r'^puzzle_new/info/(\d+)/$',  views.puzzle_new_info, name='puzzles.views.puzzle_new_info'),
    re_path(r'^puzzle/info/(\d+)/$',  views.puzzle_info, name='puzzles.views.puzzle_info'),
    re_path(r'^puzzle/spreadsheet/(\d+)/$',  views.puzzle_spreadsheet, name='puzzles.views.puzzle_spreadsheet'),
    re_path(r'^puzzle/chat/(\d+)/$',  views.puzzle_chat, name='puzzles.views.puzzle_chat'),
    re_path(r'^puzzle/set_status/(\d+)/$',  views.puzzle_set_status, name='puzzles.views.puzzle_set_status'),
    re_path(r'^puzzle/set_priority/(\d+)/$',  views.puzzle_set_priority, name='puzzles.views.puzzle_set_priority'),
    re_path(r'^puzzle/remove_solver/(\d+)/$',  views.puzzle_remove_solver, name='puzzles.views.puzzle_remove_solver'),
    re_path(r'^puzzle/add_solver/(\d+)/$',  views.puzzle_add_solver, name='puzzles.views.puzzle_add_solver'),
    re_path(r'^puzzle/upload/(\d+)/$',  views.puzzle_upload, name='puzzles.views.puzzle_upload'),
    re_path(r'^puzzle/call_in_answer/(\d+)/$',  views.puzzle_call_in_answer, name='puzzles.views.puzzle_call_in_answer'),
    re_path(r'^puzzle/request_hint/(\d+)/$',  views.puzzle_request_hint, name='puzzles.views.puzzle_request_hint'),
    re_path(r'^puzzle/history/(\d+)/$',  views.puzzle_view_history, name='puzzles.views.puzzle_view_history'),
    re_path(r'^puzzle/jitsi/(\d+)/$',  views.puzzle_jitsi_page, name='puzzles.views.puzzle_jitsi_page'),
    re_path(r'^notapuzzle/jitsi/(\w+)/$',  views.jitsi_page, name='puzzles.views.jitsi_page'),
    re_path(r'^puzzle/linkout/(\d+)/$',  views.puzzle_linkout, name='puzzles.views.puzzle_linkout'),
    
    re_path(r'^iworkallnightandiaccept8x8jaaswebhooksallday',views.jaas_webhook),

    re_path(r'^puzzle/user_location/$',  views.user_location, name='puzzles.views.user_location'),
    re_path(r'^puzzle/go_to_sleep/$',  views.go_to_sleep, name='puzzles.views.go_to_sleep'),

    re_path(r'^answers/$',  views.answer_queue, name='puzzles.views.answer_queue'),
    re_path(r'^answer/(\d+)/([a-z]+)/$',  views.answer_submit_result, name='puzzles.views.answer_submit_result'),
    re_path(r'^hints/$',  views.hint_queue, name='puzzles.views.hint_queue'),
    re_path(r'^hint/(\d+)/$',  views.hint_resolve, name='puzzles.views.hint_resolve'),

    re_path(r'^logout/$',  views.logout_user, name='puzzles.views.logout_user'),
    re_path(r'^logout_return/$',  views.logout_return, name='puzzles.views.logout_return'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # re_path(r'^admin/doc/', include('django.contrib.admindocs.re_paths')),

    path('', include('social_django.urls', namespace='social')),

    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^privacy/',RedirectView.as_view(url=settings.PRIVACY_URL),name='privacy'),
    re_path(r'^help/',RedirectView.as_view(url=settings.HELP_URL),name='help'),
    re_path(r'^generalhelp/',RedirectView.as_view(url=settings.GENERALHELP_URL),name='generalhelp'),
]
