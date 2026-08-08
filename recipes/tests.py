from django.test import TestCase
from .models import Recipe
from .parsing import parse_recipe_text


class ParseRecipeTextTests(TestCase):
    """parse_recipe_text is a pure function — no database, no request, just
    input text in and a dict out. Good place to start: no Django test
    machinery to think about yet, just plain assertions.
    """

    def test_parses_name_and_sections(self):
        text = (
            "Name: Test Recipe\n"
            "Ingredients:\n"
            "1 egg\n"
            "2 cups flour\n"
            "Instructions:\n"
            "Mix it.\n"
            "Bake it.\n"
        )
        # TODO (me): call parse_recipe_text(text) and assert on the
        # resulting dict — check fields["name"], and that fields["ingredients"]
        # / fields["instructions"] contain what you'd expect (remember: they're
        # stored as newline-joined strings, not lists — see models.py).

    def test_missing_name_raises(self):
        text = "Ingredients:\n1 egg\n"
        # TODO (me): parse_recipe_text should raise ValueError when there's
        # no "Name:" line. Look up self.assertRaises — it's a context manager:
        #   with self.assertRaises(ValueError):
        #       parse_recipe_text(text)


class RecipeModelTests(TestCase):
    def test_str_returns_name(self):
        recipe = Recipe.objects.create(name="Garlic Butter Pasta")
        # TODO (me): assert str(recipe) equals "Garlic Butter Pasta".
        # (self.assertEqual(a, b) is the standard way.)


class RecipeListViewTests(TestCase):
    def test_list_shows_recipe_names(self):
        Recipe.objects.create(name="Garlic Butter Pasta")
        # TODO (me): use self.client.get("/recipes/") to fetch the list page,
        # then assert response.status_code == 200 and that b"Garlic Butter
        # Pasta" appears in response.content. (It's bytes, not a str —
        # that's why the b"..." prefix.)

    def test_favorited_recipe_sorts_first(self):
        Recipe.objects.create(name="Zucchini Bread")
        Recipe.objects.create(name="Apple Pie", is_favorite=True)
        # TODO (me): fetch "/recipes/" and check that "Apple Pie" appears
        # in response.content *before* "Zucchini Bread" — even though
        # alphabetically Apple comes first anyway, so this test as written
        # doesn't actually prove favorites-first works! Think about how to
        # pick two recipe names where alphabetical order and favorite order
        # would disagree, so the test would actually fail if the favorite
        # sorting broke.
