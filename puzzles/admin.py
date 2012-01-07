from django.contrib import admin
from puzzles.models import Status, Priority, Tag, Puzzle

class SlugAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text',)}
admin.site.register(Status, SlugAdmin)
admin.site.register(Priority, SlugAdmin)
admin.site.register(Tag)
admin.site.register(Puzzle)
