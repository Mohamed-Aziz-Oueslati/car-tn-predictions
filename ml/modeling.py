from ml import preprocessing as pp
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import GridSearchCV
import mlflow
import joblib
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np
from xgboost import XGBRegressor

# Deep Learning Imports
from scikeras.wrappers import KerasRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from pytorch_tabnet.tab_model import TabNetRegressor

def create_keras_dnn(hidden_layers=2, neurons=128, learning_rate=0.001, dropout_rate=0.2):
    """Builder function for TensorFlow/Keras DNN compatible with SciKeras wrapper."""
    model = Sequential()
    # Input layer implicitly handled by SciKeras, start with first hidden layer
    model.add(Dense(neurons, activation='relu'))
    model.add(BatchNormalization())
    
    # Additional Hidden Layers
    for _ in range(hidden_layers - 1):
        model.add(Dense(neurons // 2, activation='relu'))
        model.add(BatchNormalization())
        if dropout_rate > 0:
            model.add(Dropout(dropout_rate))
            
    # Output Layer for Regression
    model.add(Dense(1, activation='linear'))
    model.compile(optimizer=Adam(learning_rate=learning_rate), loss='mse', metrics=['mae'])
    return model


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
        # ------------- DEEP LEARNING MODELS -------------
        "MLPRegressor": {
            "model": MLPRegressor(random_state=42, early_stopping=True),
            "params": {
                "model__hidden_layer_sizes": [(128, 64, 32), (256, 128, 64)],
                "model__activation": ["relu", "tanh"],
                "model__learning_rate_init": [0.001, 0.01],
                "model__max_iter": [500]
            }
        },
        "Keras_DNN": {
            "model": KerasRegressor(
                model=create_keras_dnn,
                verbose=0,
                epochs=50,
                batch_size=32,
                hidden_layers=2,
                neurons=128,
                learning_rate=0.001,
                dropout_rate=0.2
            ),
            "params": {
                "model__hidden_layers": [2, 3],
                "model__neurons": [128, 256],
                "model__dropout_rate": [0.1, 0.2],
                "model__batch_size": [32, 64]
            }
        },
        "TabNet": {
            "model": TabNetRegressor(verbose=0, seed=42),
            "params": {
                "model__n_d": [8, 16],
                "model__n_a": [8, 16],
                "model__n_steps": [3, 5],
                "model__gamma": [1.3, 1.5]
            }
        }
    }
    
    best_overall_model = None
    best_overall_score = float('-inf')
    
    for name, config in models.items():
        with mlflow.start_run(run_name=f"{name}_GridSearch"):
            pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('model', config["model"])
            ])
            
            # Use n_jobs=1 for DNN/TabNet to prevent multiprocessing crashes (OOM/CUDA errors)
            # Use n_jobs=-1 for everything else.
            grid_n_jobs = 1 if name in ["Keras_DNN", "TabNet"] else -1
            
            grid_search = GridSearchCV(
                pipeline,
                config["params"],
                cv=5,
                scoring="r2",
                n_jobs=grid_n_jobs
            )
            
            grid_search.fit(X_train, y_train)
            
            best_model = grid_search.best_estimator_
            predictions = best_model.predict(X_test)
            
            mae = mean_absolute_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            
            mlflow.log_params(grid_search.best_params_)
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("r2_score", r2)
            mlflow.sklearn.log_model(best_model, name="best_model")
            
            print(f"\n{name} BEST PARAMS: {grid_search.best_params_}")
            print(f"{name} MAE: {mae}")
            print(f"{name} R2: {r2}")
            
            if r2 > best_overall_score:
                best_overall_score = r2
                best_overall_model = best_model
    
    print(f"\nSaving best model with R2: {best_overall_score}")
    joblib.dump(best_overall_model, "best_model.pkl")
    
    return best_overall_model
