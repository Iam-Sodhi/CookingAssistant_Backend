from flask import Flask, request, jsonify
import pandas as pd
import fuzzywuzzy.fuzz as fuzz
from flask_cors import CORS
import logging
logging.basicConfig(level=logging.INFO)


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load dataset
df = pd.read_csv("df-en-final.csv")

# Filter dataset to include only relevant rows (with > 4 ingredients)
df["Ingredient-count"] = df["P-Ingredients"].apply(lambda x: len(x.split(",")))
df = df[df["Ingredient-count"] > 4]
df.reset_index(drop=True, inplace=True)

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

if __name__ == '__main__':
    app.run(debug=True)
