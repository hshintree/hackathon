import modal

app = modal.App("gigadataset-embed")

image = modal.Image.debian_slim().pip_install([
    "transformers",
    "sentence-transformers",
    "torch",
])

@app.function(image=image, timeout=600)
def embed_texts_384(texts: list, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> list:
    from transformers import AutoTokenizer, AutoModel
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    embeddings = []
    batch_size = 128
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        with torch.no_grad():
            inputs = tokenizer(batch, padding=True, truncation=True, return_tensors="pt")
            outputs = model(**inputs)
            last_hidden = outputs.last_hidden_state
            attention_mask = inputs['attention_mask'].unsqueeze(-1)
            masked = last_hidden * attention_mask
            sum_embeddings = masked.sum(dim=1)
            sum_mask = attention_mask.sum(dim=1)
            vecs = (sum_embeddings / sum_mask).cpu().tolist()
            embeddings.extend(vecs)
    return embeddings 