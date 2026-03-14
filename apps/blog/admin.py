from django.contrib import admin

from .models import Category, Tag, Post, Comment


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name_en",)}
    list_display = ("name_en", "name_ru", "name_kk", "slug")
    search_fields = ("name_en", "name_ru", "name_kk", "slug")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "slug", "author", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "slug", "body")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("body",)
