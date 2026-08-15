from datetime import date
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from PIL import Image, ImageOps


def recipe_image_upload_path(instance, filename):
    """upload_to callable for Recipe.image — controls where/what an uploaded
    image is named. Called with the Recipe instance, so instance.name is
    available even for a brand-new (unsaved, no pk yet) recipe.

    Every recipe image is normalized to JPEG in Recipe._process_image, so the
    extension here should always be ".jpg" regardless of what was
    uploaded/fetched. If two recipes slugify to the same name, Django's
    storage backend appends a random suffix automatically — no need to
    handle that collision case here.
    """
    return f"recipes/{slugify(instance.name)}.jpg"


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

    image = models.ImageField(upload_to=recipe_image_upload_path, blank=True)

    is_favorite = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.image:
            if self.pk:
                old = Recipe.objects.filter(pk=self.pk).first()
                image_changed = not old or old.image.name != self.image.name
            else:
                image_changed = True
            if image_changed:
                self._process_image()
        super().save(*args, **kwargs)

    def _process_image(self):
        """Resize/reorient/convert self.image in place using Pillow, then
        point self.image at the processed bytes. save=False here just
        updates the field in memory — it does not recurse back into
        Recipe.save().
        """
        image = Image.open(self.image)
        image = ImageOps.exif_transpose(image)  # bake in EXIF rotation as real pixels
        image = image.convert("RGB")  # JPEG has no alpha channel; drops PNG transparency etc.
        image.thumbnail((1200, 1200))  # shrinks to fit, preserves aspect ratio, never enlarges

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        self.image.save(f"{slugify(self.name)}.jpg", ContentFile(buffer.getvalue()), save=False)

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
