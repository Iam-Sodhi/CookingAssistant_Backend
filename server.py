from flask import Flask, request, jsonify
import pandas as pd
import fuzzywuzzy.fuzz as fuzz
from flask_cors import CORS
import time
import logging
import threading
import requests 
import json

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load dataset
df = pd.read_csv("df-en-final.csv")

# Filter dataset to include only relevant rows (with > 4 ingredients)
df["Ingredient-count"] = df["P-Ingredients"].apply(lambda x: len(x.split(",")))
df = df[df["Ingredient-count"] > 4]
df.reset_index(drop=True, inplace=True)

#. Recipe Prediction
def recommend_dishes(user_ingredients, top_n=10):
    def MainCook(Pingredients):
        """Calculate fuzzy match score."""
        score = 0
        for i in set(Pingredients.split(",")):
            for j in user_ingredients.split(","):
                score += fuzz.token_set_ratio(i, j) > 80
        return score

    def MissingAndMatching(Pingredients):
        """Find missing and matching ingredients."""
        missing_ingredients = []
        matching_ingredients = []
        for i in set(Pingredients.split(",")):
            if any(fuzz.token_set_ratio(i, j) > 80 for j in user_ingredients.split(",")):
                matching_ingredients.append(i)
            else:
                missing_ingredients.append(i)
        return ", ".join(missing_ingredients), ", ".join(matching_ingredients)

    # Copy dataset to work on
    df_filtered = df.copy()

    # Find missing and matching ingredients
    df_filtered[["Missing", "Matching"]] = df_filtered["P-Ingredients"].apply(
        lambda x: pd.Series(MissingAndMatching(x))
    )

    # Exclude rows with no matches
    df_filtered = df_filtered[df_filtered["Matching"].str.strip() != ""]

    # Calculate fuzzy match score
    df_filtered["Fuzzy Match Score"] = df_filtered["P-Ingredients"].apply(MainCook)

    # Calculate missing ingredient count
    df_filtered["Missing Count"] = df_filtered["Missing"].apply(lambda x: len(x.split(",")) if x else 0)

    # Calculate final rank (higher match score is better, lower missing count is better)
    df_filtered["Ranked"] = df_filtered["Fuzzy Match Score"] - df_filtered["Missing Count"]

    # Sort by rank (descending)
    df_filtered = df_filtered.sort_values(by=["Ranked", "Fuzzy Match Score"], ascending=[False, False])

    # Return top N results with additional columns
    return df_filtered[["TranslatedRecipeName", "Missing", "Matching", "image-url", "TotalTimeInMins"]].head(top_n).to_dict(orient="records")


# Quantity Estimation
# Load recipe data from your JSON file
def load_recipe_data():
    with open("recipe_data.json", "r", encoding="utf-8") as file:
        return json.load(file)

# Adjust ingredient quantities based on the desired number of servings
def adjust_ingredient_quantities(ingredients, default_servings, desired_servings):
    adjusted_ingredients = []
    for ingredient in ingredients:
        adjusted_ingredient = ingredient.copy()

        # Only adjust if the quantity is not "as required"
        if ingredient["Quantity"].lower() != "as required":
            # If the quantity is a number (not "as required"), adjust it
            try:
                original_quantity = float(adjusted_ingredient["Quantity"])
                adjusted_quantity = original_quantity * (desired_servings / default_servings)
                adjusted_ingredient["Quantity"] = round(adjusted_quantity, 2)
            except ValueError:
                # If the quantity is a complex value (e.g., "1/2"), handle separately
                pass

        adjusted_ingredients.append(adjusted_ingredient)
    
    return adjusted_ingredients


@app.route('/')
def home():
    return jsonify({"message": "Server is running"}), 200

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        logging.info("Request received.")
        # Parse input JSON
        data = request.json
        logging.info(f"Request data: {data}")
        user_ingredients = data.get('ingredients', '')
        top_n = data.get('top_n', 10)

        # Call recommendation function
        results = recommend_dishes(user_ingredients, top_n)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/quantity_estimation', methods=['POST'])
def adjust_recipe():
    try:
        # Parse the input JSON
        data = request.json
        recipe_name = data.get("recipe_name")
        desired_servings = data.get("desired_servings")

        # Load the recipe data from JSON
        recipe_data = load_recipe_data()

        # Check if the recipe exists in the data
        if recipe_name not in recipe_data:
            return jsonify({"status": "error", "message": "Recipe not found"}), 404

        # Get the default recipe details
        recipe = recipe_data[recipe_name]
        default_servings = recipe["DefaultServings"]
        ingredients = recipe["Ingredients"]

        # Adjust ingredients for the desired servings
        adjusted_ingredients = adjust_ingredient_quantities(ingredients, default_servings, desired_servings)

        return jsonify({
            "status": "success",
            "recipe_name": recipe_name,
            "desired_servings": desired_servings,
            "ingredients": adjusted_ingredients
        })
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


    
def ping_server():
    """Ping the server periodically to keep it active."""
    while True:
        try:
            logging.info("Pinging the server to keep it active...")
            response = requests.get('https://cookingassistant-backend.onrender.com')  # Replace with your actual server URL
            if response.status_code == 200:
                logging.info("Server is active and responded successfully.")
            else:
                logging.warning(f"Server responded with status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error while pinging the server: {e}")
        time.sleep(300)  # Ping every 5 minutes


if __name__ == '__main__':
    threading.Thread(target=ping_server, daemon=True).start()
    app.run(debug=True)
