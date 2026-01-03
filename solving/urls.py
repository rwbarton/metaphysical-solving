from django.urls import re_path, include, path
from django.views.generic.base import RedirectView
from puzzles import views
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    re_path(r'^$', views.welcome),

    # Endpoints

    # Endpoints for retrieving the user's own profile photo or by id
    re_path(r'^profile_photo/(\d+)$', views.profile_photo, name='puzzles.views.profile_photo_with_id'),
    re_path(r'^profile_photo', views.profile_photo, name='puzzles.views.profile_photo'),

    # All puzzles overview data, in JSON format
    re_path(r'^api_overview', views.api_overview, name="puzzles.views.api_overview"),

    # Endpoint for logging a view of a puzzle by a user
    re_path(r'^api_log_a_view/(\d+)$', views.api_log_a_view, name="puzzles.views.api_log_a_view"),

    # Updates for top-of-page announcement, JSON format
    re_path(r'^api_motd', views.api_motd, name="puzzles.views.api_motd"),

    # Single puzzle data, JSON format
    re_path(r'^api_puzzle/(\d+)$', views.api_puzzle, name='puzzles.views.api_puzzle'),

    # Single puzzle solver history, JSON format
    re_path(r'^api_puzzle_history/(\d+)$', views.api_puzzle_history, name='puzzles.views.api_puzzle_history'),

    # JSON-accepting endpoints for updating multiple puzzle fields, returns full updated puzzle data in JSON
    re_path(r'^api_update_puzzle/(\d+)$', views.api_update_puzzle, name='puzzles.views.api_update_puzzle'),

    # Multiple file upload endpoint for puzzle, returns JSON of updated file list
    re_path(r'^api_upload_files/(\d+)$', views.api_upload_files, name='puzzles.views.api_upload_files'),

    # Retrieves updated user location, JSON
    re_path(r'^api_user_location/$',  views.api_user_location, name='puzzles.views.user_location'),


    # Pages

    # All puzzles overview page
    re_path(r'^overview/$', views.overview, name='puzzles.views.overview'),

    # Who is on what puzzle page
    re_path(r'^whowhat/$', views.who_what, name='puzzles.views.who_what'),

    # Who is on what puzzle page
    re_path(r'^unloved/$', views.unloved, name='puzzles.views.unloved'),

    re_path(r'^need_zulip_login/$', views.need_zulip_login, name = 'puzzles.views.need_zulip_login'),

    # Single puzzle overview page
    re_path(r'^puzzle/(\d+)/$',  views.puzzle, name='puzzles.views.puzzle'),

    # Redirects to the puzzle's associated spreadsheet
    re_path(r'^puzzle/spreadsheet/(\d+)/$',  views.puzzle_spreadsheet, name='puzzles.views.puzzle_spreadsheet'),

    # Redirects to the puzzle's associated chat
    re_path(r'^puzzle/chat/(\d+)/$',  views.puzzle_chat, name='puzzles.views.puzzle_chat'),

    # Jitsi redirects
    re_path(r'^puzzle/jitsi/(\d+)/$',  views.puzzle_jitsi_page, name='puzzles.views.puzzle_jitsi_page'),
    re_path(r'^notapuzzle/jitsi/(\w+)/$',  views.jitsi_page, name='puzzles.views.jitsi_page'),

    # Redirects to the puzzle's external page on writing team's site, and logs the view
    # for the user.
    re_path(r'^puzzle/linkout/(\d+)/$',  views.puzzle_linkout, name='puzzles.views.puzzle_linkout'),


    re_path(r'^zulip_dm/(\d+)/$',views.zulip_dm,name='puzzles.views.zulip_dm'),
    # Jitsi webhook, called when a user joins a Jitsi room
    re_path(r'^iworkallnightandiaccept8x8jaaswebhooksallday',views.jaas_webhook),

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
