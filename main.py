import glob
import modeling

csv_files = glob.glob("*_imputed.csv")
modeling.modeling(csv_files)