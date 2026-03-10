import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def date_fix(date_str):
    if pd.isna(date_str) or date_str is None:
        return "01.1900"
    mois, annee = date_str.split(".")
    if len(mois) < 2:
        mois = "0" + mois
    if len(annee) < 4:
        annee = annee + "0"
        if len(annee) == 2:
            annee = annee + "00"
    return f"{mois}.{annee}"

def preprocessing(paths):
    df = pd.read_csv(paths[0], dtype={'Mise_en_circulation': str})
    for path in paths[1:]:
        df = pd.concat([df, pd.read_csv(path, dtype={'Mise_en_circulation': str})], ignore_index=True)
    df["Kilometrage"] = df["Kilometrage"].astype(str)
    df["Kilometrage"] = df["Kilometrage"].apply(lambda x:x.replace(" ", ""))
    df["Kilometrage"] = df["Kilometrage"].apply(lambda x: float(x))
    df["Price"] = df["Price"].apply(lambda x: float(x.split(" ")[0]))
    Q1 = df["Price"].quantile(0.25)
    Q3 = df["Price"].quantile(0.75)     
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df = df[~((df["Price"] < lower_bound) | (df["Price"] > upper_bound))]
    Q1 = df["Kilometrage"].quantile(0.25)
    Q3 = df["Kilometrage"].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df = df[~((df["Kilometrage"] < lower_bound) | (df["Kilometrage"] > upper_bound))]
    df.dropna(subset=["Price","Mise_en_circulation","Puissance_ch","Puissance_fiscale","Transmission","Carrosserie","Boite_vitesse","Energie"], inplace=True)
    df["Mise_en_circulation"] = df["Mise_en_circulation"].apply(lambda x: date_fix(x))
    print(df['Mise_en_circulation'].unique())
    df['Mise_en_circulation'] = pd.to_datetime(df['Mise_en_circulation'], format="%m.%Y")
    today = pd.Timestamp.today()
    df["age_voiture"] = (today - df["Mise_en_circulation"]).dt.days / 365.25
    
    X = df.drop(["Price", "Equipements", "Date_annonce", "URL", "Mise_en_circulation", "Title", "Modele", "Etat_general","Proprietaires"], axis=1)
    y = df["Price"]
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X.select_dtypes(include=['object']).columns.tolist()
    X[categorical_features] = X[categorical_features].apply(lambda x: x.str.upper())

    print(X["Kilometrage"])
    categorical_processing = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))
    ])
    
    numeric_preprocessing = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_preprocessing, numeric_features),
            ('cat', categorical_processing, categorical_features)
        ]
    )
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Return preprocessor along with data
    return X_train, X_test, y_train, y_test, preprocessor