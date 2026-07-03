import fasttext
from huggingface_hub import hf_hub_download


model_path = hf_hub_download(repo_id="cis-lmu/glotlid", filename="model_v3.bin")

language_model = fasttext.load_model(model_path)
