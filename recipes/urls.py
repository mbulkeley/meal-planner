from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.recipe_list, name="list"),
    path("new/", views.recipe_new, name="new"),
    path("<int:pk>/", views.recipe_detail, name="detail"),
    path("<int:pk>/edit/", views.recipe_edit, name="edit"),
    path("<int:pk>/delete/", views.recipe_delete, name="delete"),
    path("<int:pk>/favorite/", views.recipe_toggle_favorite, name="toggle_favorite"),
]
