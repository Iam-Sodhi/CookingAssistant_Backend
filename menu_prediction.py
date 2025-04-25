import json
import random

# Load recipe data from your JSON file
def load_recipe_data():
    with open("recipe_data.json", "r", encoding="utf-8") as file:
        return json.load(file)

with open("course_diet_values.json", "r") as f:
    course_diet_map = json.load(f)

preferred_diets = ["Vegetarian", "High Protein Vegetarian", "Diabetic Friendly"]


def get_meal_type(course):
    if not course:
        return "Other"
    course = course.lower()
    if "breakfast" in course or "brunch" in course:
        return "Breakfast"
    elif any(term in course for term in ["main", "lunch", "dinner", "one pot"]):
        return "Lunch/Dinner"
    elif any(term in course for term in ["snack", "appetizer", "dessert"]):
        return "Snack/Dessert"
    else:
        return "Other"

def categorize_recipes(preferred_diets=None):
    recipe_data = load_recipe_data()

    categorized = {
        "Breakfast": [],
        "Lunch/Dinner": [],
        "Side Dish": [],
        "Snack/Dessert": [],
    }

    for dish, details in recipe_data.items():
        course = details.get("course", "").lower()
        diet = details.get("diet", "").strip()

        # Skip if diet doesn't match preferred list
        if preferred_diets and diet not in preferred_diets:
            continue

        # Sort into appropriate meal category
        meal_type = get_meal_type(course)

        if meal_type == "Breakfast":
            categorized["Breakfast"].append(dish)
        elif meal_type == "Lunch/Dinner":
            categorized["Lunch/Dinner"].append(dish)
        elif meal_type == "Snack/Dessert":
            categorized["Snack/Dessert"].append(dish)
        else:
            # Optionally handle side dishes or other categories
            if "side" in course:
                categorized["Side Dish"].append(dish)
                
    return categorized


def generate_weekly_menu(preferred_diets=None):
    categorized = categorize_recipes(preferred_diets)

    breakfast_options = categorized["Breakfast"].copy()
    lunch_dinner_options = categorized["Lunch/Dinner"].copy()
    side_dish_options = categorized["Side Dish"].copy()
    snack_dessert_options = categorized["Snack/Dessert"].copy()

    random.shuffle(breakfast_options)
    random.shuffle(lunch_dinner_options)
    random.shuffle(side_dish_options)
    random.shuffle(snack_dessert_options)

    weekly_menu = []

    for day in range(1, 8):
        breakfast = breakfast_options.pop() if breakfast_options else None
        lunch = lunch_dinner_options.pop() if lunch_dinner_options else None
        dinner = lunch_dinner_options.pop() if lunch_dinner_options else None
        side_dish = side_dish_options.pop() if side_dish_options else None
        snack = snack_dessert_options.pop() if snack_dessert_options else None

        weekly_menu.append({
            "Day": f"Day {day}",
            "Breakfast": breakfast,
            "Lunch": lunch,
            "Dinner": dinner,
            "Side Dish": side_dish,
            "Snack/Dessert": snack
        })

    return weekly_menu
