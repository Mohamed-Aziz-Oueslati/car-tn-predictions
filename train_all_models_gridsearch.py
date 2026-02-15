import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor


DATA_PATH = "data/automobile_tn_data.csv"
TARGET = "price"

df = pd.read_csv(DATA_PATH)

X = df.drop(TARGET, axis=1)
y = df[TARGET]

numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
categorical_features = X.select_dtypes(include=['object']).columns

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ]
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

models = {
    "Ridge": {
        "model": Ridge(),
        "params": {
            "model__alpha": [0.1, 1.0, 10.0]
        }
    },

    "DecisionTree": {
        "model": DecisionTreeRegressor(),
        "params": {
            "model__max_depth": [None, 5, 10],
            "model__min_samples_split": [2, 5]
        }
    },

    "RandomForest": {
        "model": RandomForestRegressor(),
        "params": {
            "model__n_estimators": [100, 200],
            "model__max_depth": [None, 10]
        }
    }
}

for name, config in models.items():

    with mlflow.start_run(run_name=f"{name}_GridSearch"):

        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', config["model"])
        ])

        grid_search = GridSearchCV(
            pipeline,
            config["params"],
            cv=5,
            scoring="neg_mean_squared_error",
            n_jobs=-1
        )

        grid_search.fit(X_train, y_train)

        best_model = grid_search.best_estimator_
        predictions = best_model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)

        mlflow.log_params(grid_search.best_params_)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2_score", r2)

        mlflow.sklearn.log_model(best_model, "best_model")

        print(f"\n{name} BEST PARAMS: {grid_search.best_params_}")
        print(f"{name} RMSE: {rmse}")
        print(f"{name} R2: {r2}")
