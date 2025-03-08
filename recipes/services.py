from datetime import timedelta, date
import random
from django.utils import timezone
from django.db.models import Count
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Recipe, MealPlan, IngredientSubstitute, DietaryFilter
from .serializers import RecipeSerializer, MealPlanSerializer, IngredientSubstituteSerializer, DietaryFilterSerializer
from rest_framework.permissions import IsAuthenticated


# ✅ Generate Shopping List
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_shopping_list(request):
    user = request.user
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=7)

    meal_plans = MealPlan.objects.filter(user=user, date__range=[start_date, end_date])
    if not meal_plans.exists():
        return Response({"detail": "No meal plans found for the current week."}, status=status.HTTP_404_NOT_FOUND)

    shopping_list = {}
    for meal_plan in meal_plans:
        for recipe in meal_plan.recipes.all():
            ingredients = recipe.ingredients.split(',')
            for ingredient in ingredients:
                ingredient = ingredient.strip()
                shopping_list[ingredient] = shopping_list.get(ingredient, 0) + 1

    formatted_list = [{"ingredient": item, "quantity": quantity} for item, quantity in shopping_list.items()]
    return Response({"shopping_list": formatted_list}, status=status.HTTP_200_OK)


# ✅ Get Nutritional Summary
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritional_summary(request, recipe_id):
    try:
        recipe = Recipe.objects.get(pk=recipe_id)
        nutrition = recipe.nutrition
        summary = {key: nutrition.get(key, "N/A") for key in ["calories", "protein", "carbohydrates", "fat", "fiber"]}
        return Response({"recipe": recipe.title, "nutritional_summary": summary}, status=status.HTTP_200_OK)
    except Recipe.DoesNotExist:
        return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)


# ✅ Get Ingredient Substitute
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ingredient_substitute(request, ingredient):
    ingredient = ingredient.lower()
    try:
        substitute_entry = IngredientSubstitute.objects.get(ingredient=ingredient)
        return Response({"ingredient": ingredient, "substitutes": substitute_entry.substitutes},
                        status=status.HTTP_200_OK)
    except IngredientSubstitute.DoesNotExist:
        return Response({"ingredient": ingredient, "substitutes": ["No substitutes found."]},
                        status=status.HTTP_404_NOT_FOUND)


# ✅ Add Ingredient Substitute
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_ingredient_substitute(request):
    serializer = IngredientSubstituteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Rate Recipe
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_recipe(request, id):
    try:
        recipe = Recipe.objects.get(id=id)
        new_rating = float(request.data.get('rating'))
        if 0 <= new_rating <= 5:
            recipe.rating = new_rating
            recipe.save()
            return Response(RecipeSerializer(recipe).data, status=status.HTTP_200_OK)
        return Response({'detail': 'Rating must be between 0 and 5.'}, status=status.HTTP_400_BAD_REQUEST)
    except (Recipe.DoesNotExist, ValueError):
        return Response({'detail': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)


# ✅ Get Popular Recipes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_popular_recipes(request):
    recipes = Recipe.objects.annotate(favorites_count=Count('favorites')).order_by('-rating', '-favorites_count')[:10]
    return Response(RecipeSerializer(recipes, many=True).data, status=status.HTTP_200_OK)


# ✅ Add to Favorites
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_favorites(request, id):
    try:
        recipe = Recipe.objects.get(id=id)
        if recipe.favorites.filter(id=request.user.id).exists():
            return Response({"detail": "Already in favorites."}, status=status.HTTP_400_BAD_REQUEST)
        recipe.favorites.add(request.user)
        return Response({"detail": "Added to favorites."}, status=status.HTTP_200_OK)
    except Recipe.DoesNotExist:
        return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)


# ✅ Get Dietary Filters
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dietary_filters(request):
    return Response(DietaryFilterSerializer(DietaryFilter.objects.all(), many=True).data, status=status.HTTP_200_OK)


# ✅ Get Today's Meal Plan
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_today_meal_plan(request):
    meal_plan = MealPlan.objects.filter(user=request.user, date=timezone.now().date()).first()
    if not meal_plan:
        return Response({'detail': 'No meal plan found for today.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(MealPlanSerializer(meal_plan).data, status=status.HTTP_200_OK)


# ✅ Weekly Meal Plan
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def weekly_meal_plan(request):
    try:
        start_date = date.fromisoformat(request.data.get("start_date"))
    except (TypeError, ValueError):
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    meal_plans = []
    for i in range(7):
        meal_date = start_date + timedelta(days=i)
        recipes = Recipe.objects.order_by('?')[:3]
        if not recipes.exists():
            return Response({"error": "No recipes available."}, status=status.HTTP_400_BAD_REQUEST)
        meal_plan = MealPlan.objects.create(user=user, date=meal_date)
        meal_plan.recipes.set(recipes)
        meal_plan.save()
        meal_plans.append(meal_plan)
    return Response(MealPlanSerializer(meal_plans, many=True).data, status=status.HTTP_201_CREATED)


# ✅ Recipe Views
class RecipeRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            base_recipe = Recipe.objects.get(id=id)
            other_recipes = Recipe.objects.exclude(id=id)
            recommended_recipes = random.sample(list(other_recipes), min(3, other_recipes.count()))
            return Response(RecipeSerializer(recommended_recipes, many=True).data, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)