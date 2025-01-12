from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin
from puzzles.models import Round, Status, Priority, Tag, AutoTag, TagList, UploadedFile, Location, Puzzle, SubmittedAnswer, \
    PuzzleWrongAnswer, Config, AccessLog, JitsiRooms, PuzzleFolder, PuzzleTemplate, QueuedAnswer, QueuedHint


class SlugAdmin(OrderedModelAdmin):
    list_display = ('text', 'move_up_down_links')
    prepopulated_fields = {'css_name': ('text',)}
admin.site.register(Status, SlugAdmin)
admin.site.register(Priority, SlugAdmin)

class ItemAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links')
admin.site.register(Round, ItemAdmin)
admin.site.register(Tag, ItemAdmin)
admin.site.register(TagList, ItemAdmin)
admin.site.register(Location, ItemAdmin)
class PuzzleAdmin(OrderedModelAdmin):
    list_display = ('title', 'status', 'priority', 'answer', 'move_up_down_links')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'answer')
    def get_readonly_fields(self,request, obj=None):
        if obj:
            return ['template','folder']
        else:
            return []

admin.site.register(Puzzle, PuzzleAdmin)

admin.site.register(PuzzleWrongAnswer)
class SubmittedAnswerAdmin(admin.ModelAdmin):
    list_display = ('puzzle', 'answer', 'user', 'backsolved', 'success', 'timestamp')
    list_filter = ('timestamp', 'backsolved', 'success')
    search_fields = ('answer',)
    ordering = ('-timestamp',)

admin.site.register(SubmittedAnswer, SubmittedAnswerAdmin)
admin.site.register(AutoTag)

admin.site.register(Config)
class LogAdmin(OrderedModelAdmin):
	list_display = ('user','puzzle','accumulatedMinutes','lastUpdate')
	list_filter = ('user','puzzle')
admin.site.register(AccessLog, LogAdmin)

class JitsiAdmin(OrderedModelAdmin):
	list_display = ('user','puzzle','string_id')
	list_filter = ('user','puzzle','string_id')
admin.site.register(JitsiRooms,JitsiAdmin)
class DriveAdmin(OrderedModelAdmin):
    list_display = ('name','fid')
admin.site.register(PuzzleFolder,DriveAdmin)
admin.site.register(PuzzleTemplate,DriveAdmin)

admin.site.register(UploadedFile,admin.ModelAdmin)
admin.site.register(QueuedAnswer,OrderedModelAdmin)
admin.site.register(QueuedHint,OrderedModelAdmin)