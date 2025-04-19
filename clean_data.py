import pandas as pd


df = pd.read_csv("data.csv")
# print(df.columns)
df["department"] = df["department"].astype(str).str.split(";").str[0].str.strip()
faq_data = df[["id","question","answer","department"]].to_dict(orient="records")

# Print or save the output
# print(faq_data)