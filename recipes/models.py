from django.db import models


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    author = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    # Named recipe_yield, not yield — `yield` is a reserved Python keyword and
    # can't be used as an identifier, even as a model field / attribute name.
    recipe_yield = models.CharField(max_length=50, blank=True)

    # Stored as raw ISO 8601 durations ("PT15M") rather than Django's
    # DurationField. DurationField round-trips through Python timedelta and
    # serializes back out as "0:15:00", not ISO 8601 — we'd have to convert
    # it for every render. Storing the string schema.org actually wants
    # avoids that conversion entirely, at the cost of no built-in validation.
    prep_time = models.CharField(max_length=20, blank=True)
    cook_time = models.CharField(max_length=20, blank=True)
    total_time = models.CharField(max_length=20, blank=True)

    recipe_category = models.CharField(max_length=100, blank=True)

    # One item per line; split on render. See recipe.html for the target markup.
    ingredients = models.TextField(blank=True)
    instructions = models.TextField(blank=True)

    image = models.ImageField(upload_to="recipes/", blank=True)

    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return self.name
