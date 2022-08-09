""""""
import os

import torch
from transformers import AutoTokenizer, AutoModel

model_path = os.environ.get("VELO_MODEL_PATH", "/model/")

tokenizer = AutoTokenizer.from_pretrained(model_path)

model = AutoModel.from_pretrained(model_path)
# model.cuda()  # uncomment it if you have a GPU


def embed_bert_cls(text):
    t = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        model_output = model(**{k: v.to(model.device) for k, v in t.items()})
    embeddings = model_output.last_hidden_state[:, 0, :]
    embeddings = torch.nn.functional.normalize(embeddings)
    return embeddings[0].cpu().numpy()
