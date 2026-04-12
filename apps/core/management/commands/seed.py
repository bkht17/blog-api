import random
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.utils.text import slugify

from apps.blog.models import Category, Post, PostStatus, Tag

import logging

logger = logging.getLogger("blog")

User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with test data"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Post.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()

        self.stdout.write("Seeding database...")
        self._create_users()
        tags = self._create_tags()
        cat = self._create_category()
        self._create_posts(cat, tags)
        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))

    def _create_users(self) -> None:
        admin, created = User.objects.get_or_create(
            email="admin@blog.com",
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            logger.info("Created admin user: %s", admin.email)

        user, created = User.objects.get_or_create(
            email="user@blog.com",
            defaults={"first_name": "Test", "last_name": "User"},
        )
        if created:
            user.set_password("user123")
            user.save()
            logger.info("Created regular user: %s", user.email)

    def _create_tags(self) -> list[Tag]:
        tags = []
        for name in ("python", "django", "api", "celery", "redis"):
            tag, _ = Tag.objects.get_or_create(name=name, slug=name)
            tags.append(tag)
        return tags

    def _create_category(self) -> Category:
        desired = {
            "slug": "tech",
            "name_en": "Technology",
            "name_ru": "Технологии",
            "name_kk": "Технология",
        }
        cat = (
            Category.objects.filter(slug=desired["slug"]).first()
            or Category.objects.filter(name_en=desired["name_en"]).first()
            or Category.objects.filter(name_ru=desired["name_ru"]).first()
            or Category.objects.filter(name_kk=desired["name_kk"]).first()
        )
        if cat is not None:
            for field, value in desired.items():
                setattr(cat, field, value)
            cat.save()
            return cat
        return Category.objects.create(**desired)

    def _create_posts(self, category: Category, tags: list[Tag]) -> None:
        admin = User.objects.get(email="admin@blog.com")
        for i in range(1, 6):
            title = f"Test Post {i}"
            post, created = Post.objects.get_or_create(
                slug=slugify(title),
                defaults={
                    "author": admin,
                    "title": title,
                    "body": f"This is the body of test post number {i}.",
                    "category": category,
                    "status": PostStatus.PUBLISHED,
                },
            )
            if created:
                post.tags.set(random.sample(tags, k=2))
                logger.info("Created post: %s", post.slug)
