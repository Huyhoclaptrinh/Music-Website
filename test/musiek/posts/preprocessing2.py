# from django_pandas.io import read_frame
# from .models import UserSongInteraction, Music
# from surprise import Dataset
# from surprise import Reader

# from surprise import SVD
# from surprise import accuracy
# from surprise.model_selection import GridSearchCV
# from surprise.model_selection import train_test_split

# def preprocess_data():
#     # Load user-song interaction data from UserSongInteraction model
#     interactions_qs = UserSongInteraction.objects.all()
#     interactions_df = read_frame(interactions_qs)

#     # Convert to Surprise-compatible DataFrame
#     interactions_df.rename(columns={'user': 'user_id', 'music': 'music_id'}, inplace=True)
#     print(interactions_df)
#     # Define the rating scale for Surprise library
#     reader = Reader(rating_scale=(0, 1))

#     # Create a Surprise dataset from the interactions data
#     data = Dataset.load_from_df(interactions_df[['user_id', 'music_id', 'likes']], reader)
#     print(data)

#     return data

# def train_model(trainset, model):
#     # Train the model on the training set
#     model.fit

#     return model

# def tune_hyperparameters(data):
#     # Split the data into training and testing sets
#     trainset, testset = train_test_split(data, test_size=0.2)

#     # Define the algorithm
#     algorithm = SVD

#     # Define the hyperparameters to tune
#     param_grid = {'n_epochs': [5, 10, 15], 'lr_all': [0.002, 0.005, 0.01], 'reg_all': [0.4, 0.6, 0.8]}

#     # Perform grid search to find the best hyperparameters
#     gs = GridSearchCV(algorithm, param_grid, measures=['rmse'], cv=3)
#     gs.fit(data)

#     # Get the best model and its RMSE score
#     best_model = gs.best_estimator['rmse']
#     best_score = gs.best_score['rmse']

#     return best_model, best_score

# def make_recommendations(user_id, model, top_n=5):
#     # Make recommendations for a specific user
#     recommendations = []

#     for item_id in range(model.trainset.n_items):
#         # Predict the rating for the item
#         prediction = model.predict(user_id, item_id)

#         # Add the item ID and predicted rating to the recommendations list
#         recommendations.append((item_id, prediction.est))

#     # Sort the recommendations by predicted rating
#     recommendations.sort(key=lambda x: x[1], reverse=True)

#     # Get the top N recommended item IDs
#     item_ids = [item_id for item_id, _ in recommendations[:top_n]]

#     return item_ids