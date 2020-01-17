from django.urls import re_path, include, path
from puzzles import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    re_path(r'^$', views.welcome),

    re_path(r'^overview/$', views.overview, name='puzzles.views.overview'),
    re_path(r'^overview/(\d+)/$',  views.overview_by, name='puzzles.views.overview_by'),

    re_path(r'^puzzle/(\d+)/$',  views.puzzle, name='puzzles.views.puzzle'),
    re_path(r'^puzzle/info/(\d+)/$',  views.puzzle_info, name='puzzles.views.puzzle_info'),
    re_path(r'^puzzle/spreadsheet/(\d+)/$',  views.puzzle_spreadsheet, name='puzzles.views.puzzle_spreadsheet'),
    re_path(r'^puzzle/chat/(\d+)/$',  views.puzzle_chat, name='puzzles.views.puzzle_chat'),
    re_path(r'^puzzle/set_status/(\d+)/$',  views.puzzle_set_status, name='puzzles.views.puzzle_set_status'),
    re_path(r'^puzzle/set_priority/(\d+)/$',  views.puzzle_set_priority, name='puzzles.views.puzzle_set_priority'),
    re_path(r'^puzzle/remove_solver/(\d+)/$',  views.puzzle_remove_solver, name='puzzles.views.puzzle_remove_solver'),
    re_path(r'^puzzle/add_solver/(\d+)/$',  views.puzzle_add_solver, name='puzzles.views.puzzle_add_solver'),
    re_path(r'^puzzle/upload/(\d+)/$',  views.puzzle_upload, name='puzzles.views.puzzle_upload'),
    re_path(r'^puzzle/call_in_answer/(\d+)/$',  views.puzzle_call_in_answer, name='puzzles.views.puzzle_call_in_answer'),

    re_path(r'^puzzle/user_location/$',  views.user_location, name='puzzles.views.user_location'),
    re_path(r'^puzzle/go_to_sleep/$',  views.go_to_sleep, name='puzzles.views.go_to_sleep'),

    re_path(r'^answers/$',  views.answer_queue, name='puzzles.views.answer_queue'),
    re_path(r'^answer/(\d+)/([a-z]+)/$',  views.answer_submit_result, name='puzzles.views.answer_submit_result'),

    re_path(r'^logout/$',  views.logout_user, name='puzzles.views.logout_user'),
    re_path(r'^logout_return/$',  views.logout_return, name='puzzles.views.logout_return'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # re_path(r'^admin/doc/', include('django.contrib.admindocs.re_paths')),

    path('', include('social_django.urls', namespace='social')),

    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls),
]
