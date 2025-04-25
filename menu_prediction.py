# menu_prediction.py
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
    elif any(term in course for term in ["main", "lunch", "dinner", "side", "one pot"]):
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
    }

    for dish, details in recipe_data.items():
        course = details.get("course", "").lower()
        diet = details.get("diet", "").strip()

        # Skip if diet doesn't match preferred list
        if preferred_diets and diet not in preferred_diets:
            continue

        # Sort into appropriate meal category
        if "breakfast" in course:
            categorized["Breakfast"].append(dish)
        elif any(k in course for k in ["lunch", "dinner", "main course", "side dish", "one pot dish"]):
            categorized["Lunch/Dinner"].append(dish)

    return categorized


def generate_weekly_menu(preferred_diets=None):
    categorized = categorize_recipes(preferred_diets)

    breakfast_options = categorized["Breakfast"].copy()
    lunch_dinner_options = categorized["Lunch/Dinner"].copy()

    random.shuffle(breakfast_options)
    random.shuffle(lunch_dinner_options)

    weekly_menu = []

    for day in range(1, 8):
        breakfast = breakfast_options.pop() if breakfast_options else None
        lunch = lunch_dinner_options.pop() if lunch_dinner_options else None
        dinner = lunch_dinner_options.pop() if lunch_dinner_options else None

        weekly_menu.append({
            "Day": f"Day {day}",
            "Breakfast": breakfast,
            "Lunch": lunch,
            "Dinner": dinner
        })

    return weekly_menu

