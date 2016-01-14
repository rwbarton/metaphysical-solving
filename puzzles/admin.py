from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin
from puzzles.models import Status, Priority, Tag, AutoTag, TagList, Location, Puzzle, SubmittedAnswer, PuzzleWrongAnswer, Config

class SlugAdmin(OrderedModelAdmin):
    list_display = ('text', 'move_up_down_links')
    prepopulated_fields = {'css_name': ('text',)}
admin.site.register(Status, SlugAdmin)
admin.site.register(Priority, SlugAdmin)

class ItemAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links')
admin.site.register(Tag, ItemAdmin)
admin.site.register(TagList, ItemAdmin)
admin.site.register(Location, ItemAdmin)
class PuzzleAdmin(OrderedModelAdmin):
    list_display = ('title', 'move_up_down_links')
admin.site.register(Puzzle, PuzzleAdmin)

admin.site.register(PuzzleWrongAnswer)
class SubmittedAnswerAdmin(admin.ModelAdmin):
    list_display = ('puzzle', 'answer', 'user', 'backsolved', 'success', 'timestamp')

admin.site.register(SubmittedAnswer, SubmittedAnswerAdmin)
admin.site.register(AutoTag)
admin.site.register(Config)
