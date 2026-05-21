import glob
from ml import modeling

csv_files = glob.glob("automobile_tn_data_imputed.csv")
modeling.modeling(csv_files)