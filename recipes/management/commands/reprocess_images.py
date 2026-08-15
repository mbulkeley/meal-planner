from django.core.management.base import BaseCommand

from recipes.models import Recipe


class Command(BaseCommand):
    """One-off backfill: re-run Recipe._process_image against every existing
    recipe image, so recipes created before the standard naming/sizing was
    added (chilishrimp.jpeg, the raw iPhone photo) get normalized too.

    Run with: python manage.py reprocess_images

    Calls _process_image() directly and persists with a queryset .update(),
    rather than plain save() — save()'s change-detection would re-compare
    against the (still stale) DB row, see a difference, and call
    _process_image() a second time, colliding with the file the first call
    just wrote and producing a random-suffixed duplicate. .update() bypasses
    the model's save() (and its change-detection) entirely, so processing
    runs exactly once per recipe. The old file is then deleted so it doesn't
    linger as an orphan.
    """

    help = "Re-process every recipe's image (resize/reorient/rename) to the current standard."

    def handle(self, *args, **options):
        recipes = Recipe.objects.exclude(image="")
        count = 0
        for recipe in recipes:
            old_name = recipe.image.name
            recipe._process_image()
            new_name = recipe.image.name
            if new_name == old_name:
                self.stdout.write(f"{recipe.name}: unchanged ({old_name})")
                continue
            Recipe.objects.filter(pk=recipe.pk).update(image=new_name)
            recipe.image.storage.delete(old_name)
            count += 1
            self.stdout.write(f"{recipe.name}: {old_name} -> {new_name}")
        self.stdout.write(self.style.SUCCESS(f"Processed {count} recipe image(s)."))
