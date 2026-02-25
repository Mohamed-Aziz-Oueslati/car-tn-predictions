import pandas as pd

df = pd.read_csv("automobile_tn_data_imputed.csv")
print(df.Etat_general.unique())