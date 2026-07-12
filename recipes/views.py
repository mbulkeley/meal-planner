import json
import os
import re
import urllib.request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RecipeForm, RecipePasteForm
from .models import Recipe
from .parsing import parse_recipe_text

_USER_AGENT = "Mozilla/5.0 (meal-planner recipe importer)"


def _lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def _human_duration(duration):
    """Render an ISO 8601 duration ("PT1H30M") as human text ("1 hr 30 min")
    for display. The itemprop="prepTime" content= attribute keeps the raw
    ISO 8601 value — this is only for the text a person actually reads.
    """
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?$", duration)
    if not match:
        return duration  # unrecognized format — show as-is rather than hide it
    hours, minutes = match.groups()
    parts = []
    if hours:
        parts.append(f"{hours} hr")
    if minutes:
        parts.append(f"{minutes} min")
    return " ".join(parts) if parts else duration


def _fetch_url(url):
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.headers.get("Content-Type", ""), response.read()


def _fetch_image(url):
    """Best-effort image fetch for an "Image:" URL pulled from pasted recipe
    text. Accepts either a direct image link or a recipe/blog page link — for
    the latter, follows its og:image meta tag. Returns (filename, bytes), or
    None if nothing usable is found (a missing photo shouldn't block saving
    the recipe).
    """
    try:
        content_type, data = _fetch_url(url)
    except (URLError, HTTPError, ValueError):
        return None

    if not content_type.startswith("image/"):
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            data.decode("utf-8", errors="ignore"),
        )
        if not match:
            return None
        url = urljoin(url, match.group(1))
        try:
            content_type, data = _fetch_url(url)
        except (URLError, HTTPError, ValueError):
            return None
        if not content_type.startswith("image/"):
            return None

    filename = os.path.basename(urlparse(url).path) or "image.jpg"
    return filename, data


def recipe_list(request):
    recipes = Recipe.objects.order_by("-is_favorite", "name")
    return render(request, "recipes/recipe_list.html", {"recipes": recipes})


def recipe_new(request):
    error = None
    if request.method == "POST":
        form = RecipePasteForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                fields = parse_recipe_text(form.cleaned_data["text"])
            except ValueError as e:
                error = str(e)
            else:
                image_url = fields.pop("image_url", None)
                recipe = Recipe(**fields)
                uploaded_image = form.cleaned_data["image"]
                if uploaded_image:
                    recipe.image = uploaded_image
                elif image_url:
                    fetched = _fetch_image(image_url)
                    if fetched:
                        filename, data = fetched
                        recipe.image.save(filename, ContentFile(data), save=False)
                recipe.save()
                return redirect("recipes:detail", pk=recipe.pk)
    else:
        form = RecipePasteForm()
    return render(request, "recipes/recipe_new.html", {"form": form, "error": error})


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)

    ingredient_lines = _lines(recipe.ingredients)
    instruction_lines = _lines(recipe.instructions)

    recipe_json_ld = {
        "@context": "https://schema.org/",
        "@type": "Recipe",
        "name": recipe.name,
        "author": {"@type": "Organization", "name": recipe.author},
        "description": recipe.description,
        "recipeYield": recipe.recipe_yield,
        "prepTime": recipe.prep_time,
        "cookTime": recipe.cook_time,
        "totalTime": recipe.total_time,
        "recipeCategory": recipe.recipe_category,
        "recipeIngredient": ingredient_lines,
        "recipeInstructions": [
            {"@type": "HowToStep", "text": line} for line in instruction_lines
        ],
    }
    if recipe.image:
        recipe_json_ld["image"] = request.build_absolute_uri(recipe.image.url)

    context = {
        "recipe": recipe,
        "recipe_json_ld": json.dumps(recipe_json_ld),
        "ingredient_lines": ingredient_lines,
        "instruction_lines": instruction_lines,
        "prep_time_display": _human_duration(recipe.prep_time),
        "cook_time_display": _human_duration(recipe.cook_time),
        "total_time_display": _human_duration(recipe.total_time),
    }
    return render(request, "recipes/recipe_detail.html", context)


def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            return redirect("recipes:detail", pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, "recipes/recipe_edit.html", {"form": form, "recipe": recipe})


def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        recipe.delete()
        return redirect("recipes:list")
    return render(request, "recipes/recipe_delete.html", {"recipe": recipe})


def recipe_toggle_favorite(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        recipe.is_favorite = not recipe.is_favorite
        recipe.save(update_fields=["is_favorite"])
        if request.POST.get("return_to") == "list":
            return redirect("recipes:list")
    return redirect("recipes:detail", pk=recipe.pk)
