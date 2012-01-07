from django.contrib import admin
from puzzles.models import Status, Priority, Tag, TagList, TagTagListRelation, Puzzle, Motd

class SlugAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text',)}
admin.site.register(Status, SlugAdmin)
admin.site.register(Priority, SlugAdmin)
admin.site.register(Tag)
class TagTagListRelationInline(admin.TabularInline):
    model = TagTagListRelation
    extra = 1
class RelationAdmin(admin.ModelAdmin):
    inlines = (TagTagListRelationInline,)
admin.site.register(TagList, RelationAdmin)
admin.site.register(Puzzle)
admin.site.register(Motd)
