import os
import igraph as ig
import psutil
from glob import glob
from src.utils.clustering import construct_knn_graph, check_memory_constraints
from src.utils.parsing import parse_args, load_config
from src.utils.io import ensure_dirs, determine_output_filename
from src.utils.pkl_to_h5 import convert_shard

def main():
    args = parse_args()
    cfg = load_config(args)

    graph_cfg = cfg["graph_construction"]

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    embedded_directory = f'{cfg["paths"]["raw"]}/embedded'
    shard_directory = f'{cfg["paths"]["raw"]}/shards_h5'
    graph_directory = f'{cfg["paths"]["processed"]}/graphs'

    # Ensure embedding output directory exists
    os.makedirs(shard_directory, exist_ok=True)

    # Convert all pickle shards to HDF5 format
    convert_shard(embedded_directory, shard_directory)

if __name__ == '__main__':

    files = glob(os.path.join(shard_directory, '*.h5'))
    graph_file = os.path.join(graph_directory, 'article_similarity.graphml')

    print('Loading embeddings...')
    embeddings, pmids = load_embedding_shards(files)

    num_points = embeddings.shape[0]
    num_neighbors = configurations['num_neighbors']
    available_memory_gb = psutil.virtual_memory().available / (1024**3)

    # Check if the selected k will fit into memory
    if not check_memory_constraints(num_points, num_neighbors,
                                    available_memory_gb):
        raise MemoryError(
            "Not enough memory for the selected k. Please reduce k or upgrade your hardware."
        )

    print('Constructing k-NN graph...')
    edges, weights = construct_knn_graph(embeddings, num_neighbors)

    print('Creating igraph Graph object...')
    G = ig.Graph(edges=edges, directed=False)
    G.vs['pmid'] = pmids
    G.es['weight'] = weights

    print('Saving graph...')
    os.makedirs(os.path.dirname(graph_file), exist_ok=True)
    G.write(graph_file, format='graphml')