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



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_ingredient_substitute(request):
    serializer = IngredientSubstituteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_popular_recipes(request):
    recipes = Recipe.objects.annotate(favorites_count=Count('favorites')).order_by('-rating', '-favorites_count')[:10]
    return Response(RecipeSerializer(recipes, many=True).data, status=status.HTTP_200_OK)



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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dietary_filters(request):
    return Response(DietaryFilterSerializer(DietaryFilter.objects.all(), many=True).data, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_today_meal_plan(request):
    meal_plan = MealPlan.objects.filter(user=request.user, date=timezone.now().date()).first()
    if not meal_plan:
        return Response({'detail': 'No meal plan found for today.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(MealPlanSerializer(meal_plan).data, status=status.HTTP_200_OK)


def get_weekly_meal_plan(user):
    """Fetches the user's meal plan for the current week."""
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=6)

    meal_plans = MealPlan.objects.filter(user=user, date__range=[start_date, end_date])
    if not meal_plans.exists():
        return None, {"error": "No meal plans found for this week."}

    return MealPlanSerializer(meal_plans, many=True).data, None


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

def get_random_recipe():
    """Fetches a random recipe from the database."""
    return Recipe.objects.order_by('?').first()


def search_recipes_by_ingredients(ingredients):
    """Finds recipes that contain all the given ingredients."""
    ingredient_list = [ingredient.strip().lower() for ingredient in ingredients.split(',')]

    query = Q()
    for ingredient in ingredient_list:
        query &= Q(ingredients__icontains=ingredient)

    return Recipe.objects.filter(query).distinct()


def update_preferences(user, data):
    """Updates the user's dietary preferences."""
    preferences, created = UserPreferences.objects.get_or_create(user=user)
    preferences.dietary_preferences = data.get('dietary_preferences', {})
    preferences.save()

    return UserPreferencesSerializer(preferences).data
def suggest_recipes(leftovers):
    """Suggests recipes based on provided leftover ingredients."""
    if not leftovers:
        return {"detail": "No leftover ingredients provided."}, 400

    leftovers = [ingredient.lower().strip() for ingredient in leftovers]

    # Find recipes that contain at least one of the ingredients
    suggested_recipes = Recipe.objects.filter(ingredients__icontains=leftovers[0]).distinct()

    # Refine the search for multiple ingredients
    for ingredient in leftovers[1:]:
        suggested_recipes = suggested_recipes.filter(ingredients__icontains=ingredient)

    if not suggested_recipes.exists():
        return {"detail": "No recipes found using the provided ingredients."}, 404

    return RecipeSerializer(suggested_recipes, many=True).data, 200
def get_user_meal_history(user):
    """Retrieves the user's meal history and recommends new recipes."""
    meal_plans = MealPlan.objects.filter(user=user).order_by('-date')

    if not meal_plans.exists():
        return {"detail": "No meal history found."}, 404

    meal_plan_data = MealPlanSerializer(meal_plans, many=True).data

    # Get recipe IDs from the user's meal history
    recipe_ids = meal_plans.values_list('recipes', flat=True)

    # Recommend recipes NOT already in the user's history
    recommended_recipes = Recipe.objects.exclude(id__in=recipe_ids).annotate(
        rating_count=Count('rating')
    ).order_by('-rating', '-rating_count')[:5]

    recommended_data = RecipeSerializer(recommended_recipes, many=True).data

    return {"meal_history": meal_plan_data, "recommended_recipes": recommended_data}, 200
def get_recipe_nutritional_summary(recipe_id):
    """Fetches nutritional details for a specific recipe."""
    try:
        recipe = Recipe.objects.get(pk=recipe_id)
        nutrition = recipe.nutrition
        summary = {
            "calories": nutrition.get("calories", "N/A"),
            "protein": nutrition.get("protein", "N/A"),
            "carbohydrates": nutrition.get("carbohydrates", "N/A"),
            "fat": nutrition.get("fat", "N/A"),
            "fiber": nutrition.get("fiber", "N/A")
        }
        return {"recipe": recipe.title, "nutritional_summary": summary}, 200

    except Recipe.DoesNotExist:
        return {"detail": "Recipe not found."}, 404
def get_recipe_reviews(recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    reviews = RecipeReview.objects.filter(recipe=recipe)
    if not reviews.exists():
        return Response({"message": "No ratings yet"}, status=status.HTTP_200_OK)
    serializer = RecipeReviewSerializer(reviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

def create_recipe_review(recipe_id, user, data):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    data["recipe"] = recipe_id
    serializer = RecipeReviewSerializer(data=data, context={"request": user})
    if serializer.is_valid():
        serializer.save(user=user, recipe=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)