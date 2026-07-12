from datetime import date

from django.core.validators import MaxValueValidator, MinValueValidator
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


class CookLog(models.Model):
    RATING_CHOICES = [(n, "★" * n) for n in range(1, 6)]

    recipe = models.ForeignKey(Recipe, related_name="cook_logs", on_delete=models.CASCADE)
    cooked_on = models.DateField(default=date.today)
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cooked_on", "-created_at"]

    def __str__(self):
        return f"{self.recipe.name} on {self.cooked_on}"
