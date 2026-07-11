from django import forms


class RecipePasteForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label="Paste recipe text")
    image = forms.ImageField(required=False)
