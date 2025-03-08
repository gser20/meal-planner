from django.urls import path
from .views import( RecipeSearchByIngredientsView, MealPlanCreateView, RecipeCreateView,RecipeUpdateView, random_recipe, RecipeListView,
                    RecipeDeleteView, RecipeRetrieveView, RecipeSearchByIngredientsView, RecipeNutritionView, RecipeRecommendationsView, weekly_meal_plan, get_today_meal_plan,
                    get_week_meal_plan, update_user_preferences, get_dietary_filters, add_to_favorites, get_popular_recipes, rate_recipe,
                    get_ingredient_substitute,  RecipeReviewView, search_by_nutrition, get_meal_history, suggest_recipes_from_leftovers, generate_shopping_list, add_ingredient_substitute, get_nutritional_summary)   # Import the view

urlpatterns = [
    path('meal-planner/plan/', MealPlanCreateView.as_view(), name='meal-plan-create'),  # ✅ Ensure this is correct
    path('recipes/create/', RecipeCreateView.as_view(), name='recipe-create'),
    path('recipes/<int:pk>/update/', RecipeUpdateView.as_view(), name='recipe-update'),
    path('recipes/', RecipeListView.as_view(), name='recipe-list'),
    path('recipes/<int:pk>/delete/', RecipeDeleteView.as_view(), name='recipe-delete'),
    path('recipes/<int:pk>/', RecipeRetrieveView.as_view(), name='recipe-retrieve'),
    path('recipes/search-by-ingredients/', RecipeSearchByIngredientsView.as_view(), name='search-by-ingredients'),
    path('recipes/random/', random_recipe, name='random-recipe'),
    path('recipes/<int:id>/nutrition/', RecipeNutritionView.as_view(), name='recipe-nutrition'),
    path('recipes/<int:id>/recommendations/', RecipeRecommendationsView.as_view(), name='recipe-recommendations'),
    path('meal-planner/weekly/', weekly_meal_plan, name='weekly-meal-plan'),
    path('meal-planner/today/', get_today_meal_plan, name='today-meal-plan'),
    path('meal-planner/week/', get_week_meal_plan, name='week-meal-plan'),
    path('preferences/update/', update_user_preferences, name='update-user-preferences'),
    path('recipes/filters/', get_dietary_filters, name='get-dietary-filters'),
    path('recipes/<int:id>/add-to-favorites/', add_to_favorites, name='add-to-favorites'),
    path('recipes/popular/', get_popular_recipes, name='get-popular-recipes'),
    path('recipes/<int:id>/rate/', rate_recipe, name='rate-recipe'),
    path('ingredients/<str:ingredient>/substitute/', get_ingredient_substitute, name='ingredient-substitutes'),
    path('ingredients/substitute/add/', add_ingredient_substitute, name='add-ingredient-substitutes'),
    path('nutritional-info/<int:recipe_id>/summary/', get_nutritional_summary, name='nutritional-summary'),
    path('shopping-list/', generate_shopping_list, name='generate-shopping-list'),
    path('leftover-recipes/plan/', suggest_recipes_from_leftovers, name='leftover-recipes-plan'),
    path('meal-history/', get_meal_history, name='get-meal-history'),
    path('recipes/search-by-nutrition/', search_by_nutrition, name='search-by-nutrition'),
#    path('recipes/<int:id>/reviews/', get_recipe_reviews, name='get-recipe-reviews'),
 #   path('recipes/<int:id>/reviews/', add_recipe_review, name='add-recipe-review'),
    path('recipes/<int:recipe_id>/reviews/', RecipeReviewView.as_view(), name='recipe-reviews'),

]
