import pandas as pd


df = pd.read_csv("data.csv")
print(df.columns)

faq_data = df[["id","question","answer"]].to_dict(orient="records")

# Print or save the output
print(faq_data)