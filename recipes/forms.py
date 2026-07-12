from django import forms

from .models import Recipe


class RecipePasteForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label="Paste recipe text")
    image = forms.ImageField(required=False)


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            "name",
            "author",
            "description",
            "recipe_yield",
            "prep_time",
            "cook_time",
            "total_time",
            "recipe_category",
            "ingredients",
            "instructions",
            "image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "ingredients": forms.Textarea(attrs={"rows": 10}),
            "instructions": forms.Textarea(attrs={"rows": 10}),
        }
