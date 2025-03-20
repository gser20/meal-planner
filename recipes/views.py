from rest_framework import generics, status, permissions
from .models import Recipe, MealPlan, RecipeReview
from .serializers import RecipeSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import random
from .serializers import MealPlanSerializer
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import authentication_classes
from datetime import date, timedelta
from .models import UserPreferences
from .serializers import UserPreferencesSerializer
from .models import DietaryFilter
from .serializers import DietaryFilterSerializer
import logging
from django.db.models import Count
from .serializers import RecipeSerializer
from .models import IngredientSubstitute
from .serializers import IngredientSubstituteSerializer
from django.db.models import F
from django.db.models.functions import Cast
from .serializers import RecipeReviewSerializer

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def plan_meals(request):
    data = request.data
    date_str = data.get("date")

    if not date_str:
        return Response({"error": "Date is required"}, status=status.HTTP_400_BAD_REQUEST)

    date = parse_date(date_str)
    if not date:
        return Response({"error": "Invalid date format, use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

    if MealPlan.objects.filter(user=request.user, date=date).exists():
        return Response({"error": "Meal plan already exists for this date"}, status=status.HTTP_400_BAD_REQUEST)

    user_preferences = UserPreferences.objects.filter(user=request.user).first()
    dietary_tags = user_preferences.dietary_preferences.get("tags", []) if user_preferences else []

    if dietary_tags:
        recipes = Recipe.objects.filter(dietary_tags__overlap=dietary_tags)[:3]
    else:
        recipes = Recipe.objects.all()[:3]

    if not recipes.exists():
        return Response({"error": "No suitable recipes found based on your preferences"}, status=status.HTTP_404_NOT_FOUND)

    meal_plan = MealPlan.objects.create(user=request.user, date=date)
    meal_plan.recipes.set(recipes)
    meal_plan.save()

    print(f"MealPlan object: {meal_plan.__dict__}")

    # 🚀 Debugging: Print the serialized MealPlan data
    serializer = MealPlanSerializer(meal_plan)
    print(f"Serialized MealPlan Data: {json.dumps(serializer.data, indent=2)}")

    return Response(serializer.data, status=status.HTTP_201_CREATED)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dietary_filters(request):
    filters = DietaryFilter.objects.all()
    serializer = DietaryFilterSerializer(filters, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_preferences(request):
    user = request.user
    data = request.data
    preferences, created = UserPreferences.objects.get_or_create(user=user)
    preferences.dietary_preferences = data.get('dietary_preferences', {})
    preferences.save()
    serializer = UserPreferencesSerializer(preferences)
    return Response(serializer.data, status=status.HTTP_200_OK)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_week_meal_plan(request):
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=6)
    user = request.user
    meal_plans = MealPlan.objects.filter(user=user, date__range=[start_date, end_date])
    if not meal_plans.exists():
        return Response({'detail': 'No meal plans found for this week.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = MealPlanSerializer(meal_plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

class RecipeReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, recipe_id):
        if not Recipe.objects.filter(id=recipe_id).exists():
            return Response({"error": "Recipe not found"}, status=status.HTTP_404_NOT_FOUND)
        reviews = RecipeReview.objects.filter(recipe_id=recipe_id)
        if not reviews.exists():
            return Response({"message": "No ratings yet"}, status=status.HTTP_200_OK)
        serializer = RecipeReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({"error": "Recipe not found"}, status=status.HTTP_404_NOT_FOUND)
        request.data["recipe"] = recipe_id
        serializer = RecipeReviewSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_by_nutrition(request):
    goal = request.query_params.get('goal', '').lower()
    recipes = Recipe.objects.all()
    filtered_recipes = []
    for recipe in recipes:
        if isinstance(recipe.nutrition, dict):
            try:
                protein = int(str(recipe.nutrition.get("protein", "0")).replace("g", ""))
                calories = int(str(recipe.nutrition.get("calories", "0")).replace("g", ""))
                carbs = int(str(recipe.nutrition.get("carbs", "0")).replace("g", ""))
                fat = recipe.nutrition.get("fat") or recipe.nutrition.get("fats", "0")
                fat = int(str(fat).replace("g", ""))

                if goal == 'high-protein' and protein >= 40:
                    filtered_recipes.append(recipe)
                elif goal == 'low-protein' and protein <= 20:
                    filtered_recipes.append(recipe)
                elif goal == 'low-calorie' and calories <= 400:
                    filtered_recipes.append(recipe)
                elif goal == 'low-fat' and fat <= 10:
                    filtered_recipes.append(recipe)
                elif goal == 'high-fat' and fat >= 20:
                    filtered_recipes.append(recipe)
                elif goal == 'high-carbs' and carbs >= 30:
                    filtered_recipes.append(recipe)
            except ValueError:
                continue
    if not filtered_recipes:
        return Response({"message": f"No recipes found for goal: '{goal}'"}, status=status.HTTP_200_OK)
    serializer = RecipeSerializer(filtered_recipes, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meal_history(request):
    user = request.user
    meal_plans = MealPlan.objects.filter(user=user).order_by('-date')
    if not meal_plans.exists():
        return Response({"detail": "No meal history found."}, status=status.HTTP_404_NOT_FOUND)

    meal_plan_serializer = MealPlanSerializer(meal_plans, many=True)
    recipe_ids = meal_plans.values_list('recipes', flat=True)
    recommended_recipes = Recipe.objects.exclude(id__in=recipe_ids).annotate(
        rating_count=Count('rating')
    ).order_by('-rating', '-rating_count')[:5]
    recommended_serializer = RecipeSerializer(recommended_recipes, many=True)
    return Response({
        "meal_history": meal_plan_serializer.data,
        "recommended_recipes": recommended_serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_recipes_from_leftovers(request):
    data = request.data
    leftovers = data.get('ingredients', [])
    if not leftovers:
        return Response({
            "detail": "No leftover ingredients provided."
        }, status=status.HTTP_400_BAD_REQUEST)
    leftovers = [ingredient.lower().strip() for ingredient in leftovers]
    suggested_recipes = Recipe.objects.filter(
        ingredients__icontains=leftovers[0]
    ).distinct()
    if len(leftovers) > 1:
        for ingredient in leftovers[1:]:
            suggested_recipes = suggested_recipes.filter(ingredients__icontains=ingredient)
    if not suggested_recipes.exists():
        return Response({
            "detail": "No recipes found using the provided ingredients."
        }, status=status.HTTP_404_NOT_FOUND)
    serializer = RecipeSerializer(suggested_recipes, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_shopping_list(request):
    user = request.user
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=7)
    meal_plans = MealPlan.objects.filter(user=user, date__range=[start_date, end_date])
    if not meal_plans.exists():
        return Response({
            "detail": "No meal plans found for the current week."
        }, status=status.HTTP_404_NOT_FOUND)
    shopping_list = {}
    for meal_plan in meal_plans:
        for recipe in meal_plan.recipes.all():
            ingredients = recipe.ingredients.split(',')
            for ingredient in ingredients:
                ingredient = ingredient.strip()
                if ingredient in shopping_list:
                    shopping_list[ingredient] += 1
                else:
                    shopping_list[ingredient] = 1
    formatted_list = [{"ingredient": item, "quantity": quantity} for item, quantity in shopping_list.items()]
    return Response({
        "shopping_list": formatted_list
    }, status=status.HTTP_200_OK)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritional_summary(request, recipe_id):
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

        return Response({
            "recipe": recipe.title,
            "nutritional_summary": summary
        }, status=status.HTTP_200_OK)

    except Recipe.DoesNotExist:
        return Response({
            "detail": "Recipe not found."
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ingredient_substitute(request, ingredient):
    ingredient = ingredient.lower()
    try:
        substitute_entry = IngredientSubstitute.objects.get(ingredient=ingredient)
        return Response({
            "ingredient": ingredient,
            "substitutes": substitute_entry.substitutes
        }, status=status.HTTP_200_OK)
    except IngredientSubstitute.DoesNotExist:
        return Response({
            "ingredient": ingredient,
            "substitutes": ["No substitutes found."]
        }, status=status.HTTP_404_NOT_FOUND)

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
    except Recipe.DoesNotExist:
        return Response({'detail': 'Recipe not found.'}, status=status.HTTP_404_NOT_FOUND)

    new_rating = request.data.get('rating')

    if new_rating is None:
        return Response({'detail': 'Rating is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        new_rating = float(new_rating)
        if new_rating < 0 or new_rating > 5:
            raise ValueError
    except ValueError:
        return Response({'detail': 'Rating must be a number between 0 and 5.'}, status=status.HTTP_400_BAD_REQUEST)
    recipe.rating = new_rating
    recipe.save()
    serializer = RecipeSerializer(recipe)
    return Response(serializer.data, status=status.HTTP_200_OK)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_popular_recipes(request):
    recipes = Recipe.objects.annotate(
        favorites_count=Count('favorites')
    ).order_by('-rating', '-favorites_count')[:10]
    serializer = RecipeSerializer(recipes, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_favorites(request, id):
    try:
        recipe = Recipe.objects.get(id=id)
    except Recipe.DoesNotExist:
        return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
    if recipe.favorites.filter(id=request.user.id).exists():
        return Response({"detail": "Recipe is already in favorites."}, status=status.HTTP_400_BAD_REQUEST)
    recipe.favorites.add(request.user)
    return Response({"detail": "Recipe added to favorites."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_today_meal_plan(request):
    today = timezone.now().date()
    user = request.user
    meal_plan = MealPlan.objects.filter(user=user, date=today).first()
    if not meal_plan:
        return Response({'detail': 'No meal plan found for today.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = MealPlanSerializer(meal_plan)
    return Response(serializer.data, status=status.HTTP_200_OK)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def weekly_meal_plan(request):
    data = request.data
    start_date_str = data.get("start_date")
    if not start_date_str:
        return Response({"error": "Start date is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        start_date = date.fromisoformat(start_date_str)
    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
    user = request.user
    meal_plans = []
    for i in range(7):
        meal_date = start_date + timedelta(days=i)
        recipes = Recipe.objects.order_by('?')[:3]
        if not recipes.exists():
            return Response({"error": "No recipes available to create meal plan."}, status=status.HTTP_400_BAD_REQUEST)
        meal_plan = MealPlan.objects.create(user=user, date=meal_date)
        meal_plan.recipes.set(recipes)
        meal_plan.save()
        meal_plans.append(meal_plan)
    serializer = MealPlanSerializer(meal_plans, many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
class RecipeRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            base_recipe = Recipe.objects.get(id=id)
            other_recipes = Recipe.objects.exclude(id=id)
            recommended_recipes = random.sample(list(other_recipes), min(3, other_recipes.count()))
            serializer = RecipeSerializer(recommended_recipes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
class RecipeNutritionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
            nutrition = recipe.nutrition
            return Response(nutrition, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
class RecipeRetrieveView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]
class RecipeDeleteView(generics.DestroyAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]
class RecipeListView(generics.ListAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def random_recipe(request):
    recipes = Recipe.objects.all()

    if not recipes.exists():
        return Response({"error": "No recipes available"}, status=404)

    recipe = random.choice(recipes)
    serializer = RecipeSerializer(recipe)
    return Response(serializer.data)
class RecipeUpdateView(generics.UpdateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]
class RecipeCreateView(generics.CreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticated]
class RecipeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new recipe.
        """
        serializer = RecipeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class RecipeListView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class RecipeSearchByIngredientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ingredients_query = request.GET.get('ingredients', '')
        if not ingredients_query:
            return Response({"error": "No ingredients provided"}, status=400)

        ingredient_list = [ingredient.strip().lower() for ingredient in ingredients_query.split(',')]
        recipes = Recipe.objects.filter(ingredients__icontains=ingredient_list[0])

        for ingredient in ingredient_list[1:]:
            recipes = recipes.filter(ingredients__icontains=ingredient)

        if not recipes.exists():
            return Response({"message": "No available"}, status=200)

        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)



class MealPlanCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        dietary_preference = data.get("dietary_preference", "").lower()
        date = data.get("date")

        if not date:
            return Response({"error": "Date is required"}, status=status.HTTP_400_BAD_REQUEST)

        if dietary_preference:
            recipes = Recipe.objects.filter(dietary_tags__icontains=dietary_preference)
        else:
            recipes = Recipe.objects.all()

        if not recipes.exists():
            return Response({"error": "No recipes found for the given dietary preference"}, status=status.HTTP_404_NOT_FOUND)

        meal_plan = random.sample(list(recipes), min(3, len(recipes)))

        serializer = MealPlanSerializer(meal_plan, many=True)
        return Response({
            "date": date,
            "meals": serializer.data
        }, status=status.HTTP_201_CREATED)

