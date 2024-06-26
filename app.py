from urllib.parse import quote_plus
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import os
from pymongo import MongoClient
from bson import ObjectId ,errors
from bson import json_util
from flask import Response
import json
import requests
import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
import base64


app = Flask(__name__)
CORS(app)

# MongoDB connection setup
mongo_conn_str = os.getenv('MONGO_CONNECTION_STRING', '') + "&tls=true&tlsVersion=TLS1.2"
if not mongo_conn_str:
    raise ValueError("MongoDB connection string is not set in environment variables.")

mongo_client = MongoClient(mongo_conn_str, tlsAllowInvalidCertificates=True)
mongo_db = mongo_client['recipeDatabase']
recipes_collection = mongo_db['recipes']
user_recipes_collection = mongo_db['user_recipes']
user_favorites_collection = mongo_db['user_favorites']

# def fetch_unsplash_image_url(query, fallback_queries=None):
#     access_key = os.getenv('UNSPLASH_ACCESS_KEY')
#     if not access_key:
#         raise ValueError("Unsplash Access Key is not set in environment variables")

#     # Modify the query to include generic food-related keywords
#     query = f"{query} food"  # Add "food" to specify images related to food

#     # Generate permutations of words in the query
#     words = query.split()
#     word_permutations = ['+'.join(p) for p in permutations(words)]

#     # Try each permutation as a query
#     for permuted_query in word_permutations:
#         url = f'https://api.unsplash.com/search/photos?query={quote_plus(permuted_query)}&client_id={access_key}'
#         response = requests.get(url)
#         if response.status_code == 200:
#             data = response.json()
#             if data['results']:
#                 return data['results'][0]['urls']['regular']

#     # If no results, try the fallback queries if provided
#     if fallback_queries:
#         for fallback_query in fallback_queries:
#             url = f'https://api.unsplash.com/search/photos?query={quote_plus(fallback_query)}&client_id={access_key}'
#             response = requests.get(url)
#             if response.status_code == 200:
#                 data = response.json()
#                 if data['results']:
#                     return data['results'][0]['urls']['regular']

#     return None

# def fetch_google_image_urls(query, num_images=5):
#     # Construct the Google search URL for images
#     google_url = f"https://www.google.com/search?tbm=isch&q={quote_plus(query)}"

#     # Set headers to mimic a real browser request
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     }

#     # Send a GET request to Google
#     response = requests.get(google_url, headers=headers)

#     # Parse the HTML content of the response
#     soup = BeautifulSoup(response.text, "html.parser")

#     # Find all image elements in the parsed HTML
#     image_elements = soup.find_all("img")

#     # Extract the source URLs of the images
#     image_urls = []
#     for img in image_elements[:num_images]:
#         src = img.get("src")
#         if src:
#             image_urls.append(src)

#     return image_urls

def fetch_recipe_image(recipe_title, num_images=5):
    # Add "recipe" keyword to the query to improve relevance
    query = f"{recipe_title} recipe"

    # Fetch image URLs from Google
    image_urls = fetch_google_image_urls(query, num_images=num_images)

    return image_urls

def fetch_google_image_urls(query, num_images=5):
    # Construct the Google search URL for images
    google_url = f"https://www.google.com/search?tbm=isch&q={quote_plus(query)}"

    # Set headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    # Send a GET request to Google
    response = requests.get(google_url, headers=headers)

    # Parse the HTML content of the response
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all image elements in the parsed HTML
    image_elements = soup.find_all("img")

    # Extract the source URLs of the images
    image_urls = []
    for img in image_elements[:num_images]:
        src = img.get("src")
        if src:
            image_urls.append(src)

    # Return the last URL in the list
    if image_urls:
        return image_urls[-1]
    else:
        return None

# def fetch_recipe_image(recipe_title, num_images=5):
#     # Add "recipe" keyword to the query to improve relevance
#     query = f"{recipe_title} recipe"

#     # Fetch image URL from Google
#     image_url = fetch_google_image_urls(query, num_images=num_images)

#     return image_url


# def fetch_google_image_urls(query, num_images=5):
#     # Construct the Google search URL for images
#     google_url = f"https://www.google.com/search?tbm=isch&q={quote_plus(query)}"

#     # Set headers to mimic a real browser request
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     }

#     # Send a GET request to Google
#     response = requests.get(google_url, headers=headers)

#     # Parse the HTML content of the response
#     soup = BeautifulSoup(response.text, "html.parser")

#     # Find all image elements in the parsed HTML
#     image_elements = soup.find_all("img")

#     # Extract the source URLs of the images
#     image_urls = []
#     for img in image_elements[:num_images]:
#         src = img.get("src")
#         if src:
#             # Check if the URL is a relative URL
#             if src.startswith('/'):
#                 # Prepend the base URL of Google Images
#                 src = f"https://www.google.com{src}"
#             # Download the image data
#             image_data = download_image(src)
#             if image_data is not None:
#                 # Enhance image contrast
#                 enhanced_image_data = enhance_image_contrast(image_data)
#                 # Encode the image data to base64
#                 encoded_image = encode_image(enhanced_image_data)
#                 if encoded_image is not None:
#                     image_urls.append(encoded_image)

#     # Return the last URL in the list
#     if image_urls:
#         return image_urls[-1]
#     else:
#         return None

def download_image(url):
    # Send a GET request to download the image data
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        return None

# def enhance_image_contrast(image_data):
#     # Decode the image data using OpenCV
#     image_array = np.frombuffer(image_data, np.uint8)
#     image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
#     if image is not None:
#         # Apply image enhancement algorithms (e.g., contrast enhancement)
#         # Here, we are simply returning the original image data for demonstration
#         return image_data
#     else:
#         return None

def enhance_image_contrast(image_data):
    # Decode the image data using OpenCV
    image_array = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is not None:
        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply contrast limited adaptive histogram equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_image = clahe.apply(gray_image)
        # Convert the enhanced image back to BGR format
        enhanced_image_bgr = cv2.cvtColor(enhanced_image, cv2.COLOR_GRAY2BGR)
        # Encode the enhanced image data to JPEG format
        _, encoded_image = cv2.imencode('.jpg', enhanced_image_bgr)
        if encoded_image is not None:
            return encoded_image.tostring()
    
    return None


def encode_image(image_data):
    # Encode the image data to base64
    _, encoded_image = cv2.imencode('.jpg', image_data)
    if encoded_image is not None:
        return encoded_image.tostring()
    else:
        return None

# def fetch_recipe_image(recipe_title, num_images=5):
#     # Add "recipe" keyword to the query to improve relevance
#     query = f"{recipe_title} recipe"

#     # Fetch image URL from Google
#     image_url = fetch_google_image_urls(query, num_images=num_images)

#     return image_url
# def fetch_recipe_image(recipe_title, num_images=5):
#     try:
#         # Add "recipe" keyword to the query to improve relevance
#         query = f"{recipe_title} recipe"

#         # Fetch image URL from Google
#         image_url = fetch_google_image_urls(query, num_images=num_images)

#         return image_url
#     except Exception as e:
#         print(f"Error fetching image for recipe '{recipe_title}': {e}")
#         return None


@app.route('/get_recipe_id', methods=['GET'])
def get_recipe_id_by_name():
    recipe_name = request.args.get('name')
    if not recipe_name:
        return jsonify({'error': 'Recipe name is required as a query parameter.'}), 400

    try:
        recipe = recipes_collection.find_one({"recipe_title": {"$regex": f"^{recipe_name}$", "$options": "i"}})
        if recipe:
            return jsonify({'recipe_id': str(recipe['_id']), 'recipe_name': recipe['recipe_title']}), 200
        else:
            return jsonify({'message': 'Recipe not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Failed to fetch recipe ID'}), 500

# @app.route('/get_recipes_by_name', methods=['GET'])
# def get_recipes_by_name():
#     try:
#         recipe_name = request.args.get('recipe_name')
#         if not recipe_name:
#             return jsonify({'error': 'Recipe name is required as a query parameter.'}), 400

#         # Perform a case-insensitive search for recipes with names similar to the input
#         recipes_cursor = recipes_collection.find({"recipe_title": {"$regex": f".*{recipe_name}.*", "$options": "i"}}).limit(10)
#         recipes_list = list(recipes_cursor)

#         # Convert ObjectId to string for JSON compatibility
#         for recipe in recipes_list:
#             recipe['_id'] = str(recipe['_id'])

#         # If less than 10 recipes are found, fetch more
#         if len(recipes_list) < 10:
#             additional_recipes_cursor = recipes_collection.find({
#                 "recipe_title": {"$regex": f".*{recipe_name}.*", "$options": "i"},
#                 "_id": {"$nin": [recipe['_id'] for recipe in recipes_list]}}).limit(10 - len(recipes_list))
#             additional_recipes_list = list(additional_recipes_cursor)
#             for recipe in additional_recipes_list:
#                 recipe['_id'] = str(recipe['_id'])
#             recipes_list.extend(additional_recipes_list)

#         return jsonify({'recipes': recipes_list}), 200
#     except Exception as e:
#         return jsonify({'error': f'Failed to fetch recipes: {str(e)}'}), 500

@app.route('/get_recipes_by_name', methods=['GET'])
def get_recipes_by_name():
    try:
        recipe_name = request.args.get('recipe_name')
        if not recipe_name:
            return jsonify({'error': 'Recipe name is required as a query parameter.'}), 400

        # Perform a case-insensitive search for recipes with names similar to the input
        recipes_cursor = recipes_collection.find({"recipe_title": {"$regex": f".*{recipe_name}.*", "$options": "i"}}).limit(10)
        recipes_list = list(recipes_cursor)

        # Convert ObjectId to string for JSON compatibility
        for recipe in recipes_list:
            recipe['_id'] = str(recipe['_id'])

        # If less than 10 recipes are found, fetch more
        if len(recipes_list) < 10:
            additional_recipes_cursor = recipes_collection.find({
                "recipe_title": {"$regex": f".*{recipe_name}.*", "$options": "i"},
                "_id": {"$nin": [recipe['_id'] for recipe in recipes_list]}}).limit(10 - len(recipes_list))
            additional_recipes_list = list(additional_recipes_cursor)
            for recipe in additional_recipes_list:
                recipe['_id'] = str(recipe['_id'])
            recipes_list.extend(additional_recipes_list)

        # Fetch images from Unsplash based on recipe titles
        for recipe in recipes_list:
            recipe_title = recipe['recipe_title']
            image_url = fetch_recipe_image(recipe_title)
            if image_url:
                recipe['image_url'] = image_url

        return jsonify({'recipes': recipes_list}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch recipes: {str(e)}'}), 500


def fetch_image_url(recipe_title):
    try:
        # Prepare the search query
        search_query = recipe_title.replace(' ', '+')
        url = f"https://www.google.com/search?q={search_query}&tbm=isch"

        # Send a GET request to Google Images
        response = requests.get(url)
        response.raise_for_status()

        # Parse the response content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the image URL from the first image result
        image_url = soup.find('img')['src']

        return image_url
    except Exception as e:
        print(f"Error fetching image URL: {e}")
        return None


def load_data_from_mongodb():
    recipes_cursor = recipes_collection.find()
    return pd.DataFrame(list(recipes_cursor))

@app.route('/cuisines', methods=['GET'])
def get_unique_cuisines():
    try:
        recipes_df = load_data_from_mongodb()
        other_cuisines = recipes_df[recipes_df['Type'] == 'Other']['cuisine'].unique().tolist()
        unique_cuisines = ['Indian'] + other_cuisines
        filtered_cuisines = [cuisine for cuisine in unique_cuisines if cuisine != "nan"]
        return jsonify(filtered_cuisines)
    except Exception as e:
        return jsonify({'error': f'Failed to fetch cuisines: {str(e)}'}), 500
    
def recommend_recipes():
    data = request.get_json()
    input_ingredients = data.get('input', '')
    cuisine_types = data.get('cuisine_type', [])
    if isinstance(cuisine_types, str):
        cuisine_types = [cuisine_types.lower()]
    elif not isinstance(cuisine_types, list):
        cuisine_types = []

    recipes_df = load_data_from_mongodb()
    if recipes_df.empty:
        return jsonify({'error': 'No recipes found'}), 400

    recipes_df['ingredients'] = recipes_df['ingredients'].str.lower()
    if cuisine_types:
        filtered_recipes = recipes_df[recipes_df['Type'].str.lower().isin(cuisine_types)]
    else:
        filtered_recipes = recipes_df

    input_ingredients_set = set(ingredient.strip().lower() for ingredient in input_ingredients.split(','))

    if cuisine_types:
        filtered_recipes = recipes_df[recipes_df['cuisine'].isin(cuisine_types)]
    else:
        filtered_recipes = recipes_df

    filtered_recipes['matching_ingredients'] = filtered_recipes['ingredients'].apply(
        lambda x: sum(ingredient in input_ingredients_set for ingredient in x.split(', '))
    )

    try:
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf_vectorizer.fit_transform(filtered_recipes['ingredients'])
        input_vec = tfidf_vectorizer.transform([input_ingredients])
        cosine_similarities = linear_kernel(input_vec, tfidf_matrix).flatten()
        filtered_recipes['similarity_score'] = cosine_similarities
        filtered_recipes['rating'] = filtered_recipes.get('rating', 0).astype(float)
        filtered_recipes['combined_score'] = filtered_recipes['matching_ingredients'] * 0.5 + filtered_recipes['similarity_score'] * 0.25+ filtered_recipes['rating'] * 0.25
        recommendations = filtered_recipes.sort_values(by=['combined_score', 'matching_ingredients'], ascending=False).head(10)
    except Exception as e:
        return jsonify({'error': f'Failed to generate recommendations: {str(e)}'}), 500

    recommendations_list = []
    for _, row in recommendations.iterrows():
        image_url = fetch_recipe_image(row['recipe_title'])
        if not image_url:
            # Fallback to a default image or another source if Spoonacular doesn't return an image
            image_url = "https://example.com/default_image.jpg"
        recommendations_list.append({
            "_id": str(row['_id']), 
            "title": row['recipe_title'],
            "description": row['description'],
            "cuisine": row['cuisine'],
            "course": row['course'],
            "cook_time": row['cook_time'],
            "author": row['author'],
            "ingredients": row['ingredients'],
            "instructions": row['instructions'],
            "image_url": image_url,
            # "image_url": row.get('image_url') or fetch_unsplash_image_url(row['recipe_title']),
            "rating": row['rating']
        })

    return jsonify({'recommendations': recommendations_list})


@app.route('/recommend', methods=['POST'])
# def handle_recommend_request():
#     return recommend_recipes()
def handle_recommend_request():
    data = request.json
    print(f"Received data: {data}")
    recommendations = recommend_recipes()
    print(f"Sending back: {recommendations}")
    return recommendations

@app.route('/get_recipe', methods=['GET'])
def get_recipe():
    try:
        # Extract the recipe ID from the query parameter
        recipe_id = request.args.get('recipe_id')

        # Validate the presence of 'recipe_id'
        if not recipe_id:
            return jsonify({'error': 'Recipe ID is required as a query parameter.'}), 400

        try:
            # Attempt to convert the recipe ID to an ObjectId
            oid = ObjectId(recipe_id)
        except errors.InvalidId:
            return jsonify({'error': 'Invalid recipe ID format.'}), 400

        # Find the recipe in the database
        recipe = recipes_collection.find_one({'_id': oid})

        # Check if the recipe was found
        if not recipe:
            return jsonify({'message': 'Recipe not found'}), 404

        # Convert ObjectId to string for JSON serialization
        recipe['_id'] = str(recipe['_id'])
        image_url = fetch_recipe_image(recipe['recipe_title'])
        recipe['image_url'] = image_url

        # Return the found recipe
        return jsonify(recipe), 200

    except Exception as e:
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

@app.route('/rate_recipe', methods=['POST'])
def rate_recipe():
    try:
        recipe_name = request.json.get('recipe_name')
        recipe = recipes_collection.find_one({"recipe_title": {"$regex": f"^{recipe_name}$", "$options": "i"}})
        if not recipe:
            return jsonify({'message': 'Recipe not found'}), 404

        recipe_id = recipe['_id']
        recipes_collection.update_one({'_id': ObjectId(recipe_id)}, {'$inc': {'rating': 0.1}})
        updated_recipe = recipes_collection.find_one({'_id': ObjectId(recipe_id)})
        new_rating = updated_recipe.get('rating', 0)

        return jsonify({'message': 'Recipe rated successfully', 'new_rating': new_rating}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to rate recipe: {str(e)}'}), 500
    
    
@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    try:
        recipe_data = request.json.get('recipe')
        uid = request.json.get('uid')

        if not uid:
            return jsonify({'error': 'User ID must be provided.'}), 400

        # Validate the recipe data structure
        # Assuming all keys are present and required in the request
        required_keys = ['title', 'url', 'vote_count', 'rating', 'description', 'cuisine', 'Type', 'course', 'diet', 'cook_time', 'ingredients', 'instructions', 'author']
        for key in required_keys:
            if key not in recipe_data:
                return jsonify({'error': f'{key} is required'}), 400
            
        # Construct the document to be inserted
        recipe_document = {
            'recipe_title': recipe_data['title'],
            'url': recipe_data['url'],
            'vote_count': recipe_data['vote_count'],
            'rating': recipe_data['rating'],
            'description': recipe_data['description'],
            'cuisine': recipe_data['cuisine'],
            'Type': recipe_data['Type'],
            'course': recipe_data['course'],
            'diet': recipe_data['diet'],
            'cook_time': recipe_data['cook_time'],
            'ingredients': recipe_data['ingredients'],
            'instructions': recipe_data['instructions'],
            'author': recipe_data['author']
            # 'user_id': uid  # This field associates the recipe with the user who added it
        }

        # Insert the recipe into the 'recipes' collection
        inserted_recipe = recipes_collection.insert_one(recipe_data)

        # Prepare the document for the 'user_recipes' collection
        user_recipe_entry = {
            'user_id': uid,
            'recipe_id': inserted_recipe.inserted_id
        }

        # Insert the reference into the 'user_recipes' collection
        user_recipes_collection.insert_one(user_recipe_entry)

        return jsonify({
            'message': 'Recipe added successfully!',
            'recipe_id': str(inserted_recipe.inserted_id)
        }), 201

    except Exception as e:
        # return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500


@app.route('/my_recipes', methods=['GET'])
def get_my_recipes():
    try:
        uid = request.args.get('uid')
        if not uid:
            return jsonify({'error': 'User ID is required as a query parameter.'}), 400

        user_recipes_cursor = user_recipes_collection.find({'user_id': uid})
        # Convert cursor to list and then to a JSON string, manually handling ObjectId serialization
        recipes_list = json.loads(json_util.dumps(user_recipes_cursor))

        return Response(
            response=json.dumps(recipes_list),
            status=200,
            mimetype='application/json'
        )
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 401
    except Exception as e:
        return jsonify({'error': 'Failed to fetch recipes: {}'.format(e)}), 500

@app.route('/my_favorites', methods=['GET'])
def get_my_favorites():
    try:
        uid = request.args.get('uid')
        if not uid:
            return jsonify({'error': 'User ID is required as a query parameter.'}), 400
        favorite_recipes = user_favorites_collection.find({'user_id': uid})
        recipes_list = [str(recipe['recipe_id']) for recipe in favorite_recipes]  # Convert ObjectId to string
        # return jsonify(recipes_list), 200
        return jsonify({'recipes': recipes_list}), 200
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 401
    except Exception as e:
        return jsonify({'error': 'Failed to fetch favorite recipes: {}'.format(e)}), 500

    
@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    try:
        # Extract the UID and the recipe ID from the request
        uid = request.json.get('uid')
        recipe_id = request.json.get('recipe_id')

        # Validate the presence of 'uid' and 'recipe_id'
        if not uid or not recipe_id:
            return jsonify({'error': 'Both user ID and recipe ID must be provided.'}), 400

        # Check if the recipe exists in the recipes collection
        if not recipes_collection.find_one({'_id': ObjectId(recipe_id)}):
            return jsonify({'error': 'Recipe not found'}), 404

        # Prepare the document for the 'user_favorites' collection
        favorite_entry = {
            'user_id': uid,
            'recipe_id': ObjectId(recipe_id)
        }

        # Insert the document into the 'user_favorites' collection
        user_favorites_collection.insert_one(favorite_entry)

        # Return a success response
        return jsonify({'message': 'Recipe added to favorites successfully!'}), 201

    except ValueError as ve:
        # Return a 400 error if there's a problem with the user input
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        # Return a 500 error if an internal error occurred
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

    
@app.route('/trending_recipes', methods=['GET'])
def get_trending_recipes():
    try:
        # Fetch all recipes and sort them by 'rating' in descending order, then limit to top 20
        trending_recipes_cursor = recipes_collection.find().sort('rating', -1).limit(20)
        trending_recipes = list(trending_recipes_cursor)

        # Convert MongoDB BSON to JSON
        for recipe in trending_recipes:
            recipe['_id'] = str(recipe['_id'])  # Convert ObjectId to string for JSON compatibility
            image_url = fetch_recipe_image(recipe['recipe_title'])
            recipe['image_url'] = image_url

        return jsonify(trending_recipes), 200
    except Exception as e:
        print(f"Error fetching trending recipes: {e}")
        return jsonify({'error': 'Failed to fetch trending recipes'}), 500

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test route is working!"}), 200

if __name__ == '__main__':
    app.run(debug=True)
