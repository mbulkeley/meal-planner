from django.contrib import admin

from .models import CookLog, Recipe


class CookLogInline(admin.TabularInline):
    model = CookLog
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    inlines = [CookLogInline]


admin.site.register(Recipe, RecipeAdmin)
