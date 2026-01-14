from datasets import load_dataset
import pandas as pd
from urllib.parse import urlparse

# Load Kurdish data (CulturaX, Kurdish)
dataset = load_dataset("uonlp/CulturaX", "ku", split="train")

# Function to extract domain from URL
def extract_domain(url):
    try:
        return urlparse(url).netloc
    except Exception:
        return None

# Add domain column
dataset = dataset.map(lambda x: {"domain": extract_domain(x["url"])}, num_proc=4)

# Convert to pandas DataFrame
df = pd.DataFrame({
    "domain": list(dataset["domain"])
})

# Drop nulls
df = df.dropna()

# Count how many rows per domain
domain_counts = df.value_counts().reset_index()
domain_counts.columns = ["domain", "count"]

# Sort descending by count
domain_counts = domain_counts.sort_values(by="count", ascending=False).reset_index(drop=True)

# Save to CSV
domain_counts.to_csv("kurdish_domains.csv", index=False)

print(f"✅ Saved {len(domain_counts)} domains with counts to kurdish_domains.csv")
print(domain_counts.head(10))
