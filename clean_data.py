import pandas as pd

# Load data
df = pd.read_csv("data.csv")

# Fix typo manually
df["department"] = df["department"].astype(str).str.strip()
df["department"] = df["department"].replace("Genreal", "General")

# Keep only the first part before ;
df["department"] = df["department"].str.split(";").str[0].str.strip()

# Optional: Standardize capitalization
df["department"] = df["department"].str.title()

# Create dict
faq_data = df[["id", "question", "answer", "department"]].to_dict(orient="records")

# Debug: See what's missing
print("\n[Unique Departments]:", df["department"].unique())
