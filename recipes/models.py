from django.db import models
from django.contrib.auth.models import User

# No need to import Recipe here because it's defined below
class Recipe(models.Model):
    title = models.CharField(max_length=255)
    ingredients = models.TextField()
    instructions = models.TextField()
    nutrition = models.JSONField(default=dict)
    rating = models.FloatField(default=0.0)
    favorites = models.ManyToManyField(User, related_name="favorite_recipes", blank=True)
    dietary_tags = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title

class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    recipes = models.ManyToManyField('Recipe')  # Use the string 'Recipe' to avoid circular imports

    def __str__(self):
        return f"Meal Plan for {self.user} on {self.date}"

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dietary_preferences = models.JSONField(default=dict)  # Stores preferences as JSON

    def __str__(self):
        return f"Preferences for {self.user.username}"

class DietaryFilter(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., "Vegetarian", "Gluten-Free"

    def __str__(self):
        return self.name

class IngredientSubstitute(models.Model):
    ingredient = models.CharField(max_length=255, unique=True)  # Main ingredient
    substitutes = models.JSONField(default=list)  # List of substitutes

    def __str__(self):
        return self.ingredient

class RecipeReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="reviews")
    rating = models.FloatField()
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.recipe.title} - {self.rating}"