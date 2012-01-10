from django.contrib import admin
from puzzles.models import Status, Priority, Tag, TagList, Puzzle, Motd

class SlugAdmin(admin.ModelAdmin):
    prepopulated_fields = {'css_name': ('text',)}
admin.site.register(Status, SlugAdmin)
admin.site.register(Priority, SlugAdmin)
admin.site.register(Tag)
admin.site.register(TagList)
admin.site.register(Puzzle)
admin.site.register(Motd)
