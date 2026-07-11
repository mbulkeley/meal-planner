import json

from django.shortcuts import get_object_or_404, render

from .models import Recipe


def _lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def recipe_list(request):
    recipes = Recipe.objects.all()
    return render(request, "recipes/recipe_list.html", {"recipes": recipes})


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
    }
    return render(request, "recipes/recipe_detail.html", context)
