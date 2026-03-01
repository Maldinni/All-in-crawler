import pickle
import numpy as np

file = r"D:\github\All-in-crawler\data\raw\embedded\shard_0000.pkl"

with open(file, "rb") as f:
    data = pickle.load(f)

vectors = data.embeddings

print(type(vectors))
print(vectors.shape)
print(vectors.dtype)

print("NaN:", np.isnan(vectors).sum())
print("Inf:", np.isinf(vectors).sum())

norms = np.linalg.norm(vectors, axis=1)
print("Norms:", norms[:10])

import numpy as np


np.isnan(data).sum()
np.isinf(data).sum()

norms = np.linalg.norm(data, axis=1)
print(norms[:10])

from sklearn.metrics.pairwise import cosine_similarity

cosine_similarity([data[0]], [data[1]])

from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

pca = PCA(n_components=2)
reduced = pca.fit_transform(data[:1000])

plt.scatter(reduced[:, 0], reduced[:, 1])
plt.show()

import faiss

dim = vectors.shape[1]
index = faiss.IndexFlatIP(dim)  # melhor para embeddings normalizados
index.add(vectors)

D, I = index.search(vectors[:5], 5)

print(I)
print(D)