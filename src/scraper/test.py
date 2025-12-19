import pandas as pd
df=pd.read_excel("performance_quotidienne_asfim.xlsx")
hebdo=pd.read_excel("performance_hebdomadaire_asfim.xlsx")
print('colonnes_daily :', df.columns.tolist() , 'colonnes_weekly :', hebdo.columns.tolist())