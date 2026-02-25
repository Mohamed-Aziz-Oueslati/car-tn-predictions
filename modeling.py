import preprocessing as pp
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import GridSearchCV
import mlflow
import joblib
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

def modeling(paths):
    X_train, X_test, y_train, y_test, preprocessor = pp.preprocessing(paths)
    
    models = {
        "Ridge": {
            "model": Ridge(),
            "params": {
                "model__alpha": np.logspace(-4, 3, 20),
                "model__solver": ["auto", "svd", "cholesky", "lsqr"]
            }
        },
        "LinearRegression": {
            "model": LinearRegression(),
            "params": {
                "model__fit_intercept": [True, False],
                "model__positive": [True, False]
            }
        },
        "DecisionTree": {
            "model": DecisionTreeRegressor(random_state=42),
            "params": {
                "model__max_depth": [None, 5, 10, 20, 30],
                "model__min_samples_split": [2, 5, 10],
                "model__min_samples_leaf": [1, 2, 4],
                "model__max_features": [None, "sqrt", "log2"]
            }
        },
        "RandomForest": {
            "model": RandomForestRegressor(random_state=42),
            "params": {
                "model__n_estimators": [100, 200, 300],
                "model__max_depth": [None, 10, 20, 30],
                "model__min_samples_split": [2, 5, 10],
                "model__min_samples_leaf": [1, 2, 4],
                "model__max_features": ["sqrt", "log2"]
            }
        },
        "GradientBoosting": {
            "model": GradientBoostingRegressor(random_state=42),
            "params": {
                "model__n_estimators": [100, 200, 300],
                "model__learning_rate": [0.01, 0.05, 0.1, 0.2],
                "model__max_depth": [3, 5, 7],
                "model__subsample": [0.8, 1.0],
                "model__min_samples_split": [2, 5]
            }
        },
        "XGBoost": {
            "model": XGBRegressor(random_state=42, n_jobs=-1),
            "params": {
                "model__n_estimators": [100, 200, 300],
                "model__learning_rate": [0.01, 0.05, 0.1],
                "model__max_depth": [3, 5, 7, 9],
                "model__min_child_weight": [1, 3, 5],
                "model__subsample": [0.8, 0.9, 1.0],
                "model__colsample_bytree": [0.8, 0.9, 1.0],
                "model__reg_alpha": [0, 0.1, 1],
                "model__reg_lambda": [1, 1.5, 2]
            }
        },
        "LightGBM": {
            "model": LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1),
            "params": {
                "model__n_estimators": [100, 200, 300],
                "model__learning_rate": [0.01, 0.05, 0.1],
                "model__max_depth": [3, 5, 7, 9, -1],
                "model__num_leaves": [31, 50, 70, 100],
                "model__min_child_samples": [20, 30, 50],
                "model__subsample": [0.8, 0.9, 1.0],
                "model__colsample_bytree": [0.8, 0.9, 1.0],
                "model__reg_alpha": [0, 0.1, 1],
                "model__reg_lambda": [0, 0.1, 1]
            }
        }
    }
    
    best_overall_model = None
    best_overall_score = float('-inf')
    
    for name, config in models.items():
        with mlflow.start_run(run_name=f"{name}_GridSearch"):
            # IMPORTANT: Include preprocessor in the pipeline
            pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('model', config["model"])
            ])
            
            grid_search = GridSearchCV(
                pipeline,
                config["params"],
                cv=5,
                scoring="r2",
                n_jobs=-1
            )
            
            # Fit on RAW data (pipeline will handle preprocessing)
            grid_search.fit(X_train, y_train)
            
            best_model = grid_search.best_estimator_
            predictions = best_model.predict(X_test)
            
            rmse = np.sqrt(mean_squared_error(y_test, predictions))
            r2 = r2_score(y_test, predictions)
            
            mlflow.log_params(grid_search.best_params_)
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("r2_score", r2)
            mlflow.sklearn.log_model(best_model, name="best_model")
            
            print(f"\n{name} BEST PARAMS: {grid_search.best_params_}")
            print(f"{name} RMSE: {rmse}")
            print(f"{name} R2: {r2}")
            
            # Track best model
            if r2 > best_overall_score:
                best_overall_score = r2
                best_overall_model = best_model
    
    # Save the BEST model across all models
    print(f"\nSaving best model with R2: {best_overall_score}")
    joblib.dump(best_overall_model, "best_model.pkl")
    
    return best_overall_model