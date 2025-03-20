from rest_framework import serializers
from .models import MealPlan, Recipe
from .models import UserPreferences
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
        fields = '__all__'

class MealPlanSerializer(serializers.ModelSerializer):
    """Serializer for MealPlan objects"""
    recipes = RecipeSerializer(many=True, read_only=True)

    class Meta:
        model = MealPlan
        fields = ["id", "user", "date", "recipes"]
        read_only_fields = ["user", "recipes"]
class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = '__all__'

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

