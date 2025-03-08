from rest_framework import serializers
from .models import MealPlan, Recipe
from .models import UserPreferences  # ✅ Import the missing model
from .models import DietaryFilter
from .models import IngredientSubstitute
from .models import RecipeReview
class RecipeReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeReview
        fields = ["id", "user", "recipe", "rating", "review_text", "created_at"]
        read_only_fields = ["user", "created_at"]
class DietaryFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietaryFilter
        fields = ['id', 'name']
class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'  # ✅ Include all recipe details

class MealPlanSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Show username instead of user ID
    recipes = RecipeSerializer(many=True)  # ✅ Show full recipe details instead of just IDs

    class Meta:
        model = MealPlan
        fields = ['id', 'user', 'date', 'recipes']
class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = '__all__'  # Include all fields

class IngredientSubstituteSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientSubstitute
        fields = ['ingredient', 'substitutes']
class RecipeReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeReview
        fields = ['review_text', 'rating']

    def validate_rating(self, value):
        # Ensure rating is between 0 and 5
        if value < 0 or value > 5:
            raise serializers.ValidationError("Rating must be between 0 and 5.")
        return value
class RecipeReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeReview
        fields = ['id', 'recipe', 'user', 'rating', 'review_text', 'created_at']
        read_only_fields = ['user', 'created_at']  # ✅ Ensure `user` is read-only
