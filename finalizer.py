import pandas as pd
from pathlib import Path

from src.utils.parsing import parse_args, load_config
from src.utils.io import ensure_dirs

# Ordem preferida das colunas no CSV final (identidade -> descrição ->
# análise -> relacional). Colunas inesperadas são mantidas ao final.
PREFERRED_ORDER = [
    "Cluster ID",
    "Title",
    "Size",
    "Focus",
    "Keywords",
    "Description",
    "Distinguishing Features",
    "Trends",
    "Dimensions",
    "Most Similar Cluster",
    "Similarity",
]

# Valores textuais que devem ser tratados como vazios
EMPTY_TOKENS = {"nan", "NaN", "None", "null", "<NA>"}


def main():
    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    processed_path = Path(paths["processed"])
    result_file = processed_path / "clusters_defined_distinguished_trends_assessed.csv"

    if not result_file.exists():
        print(f"Arquivo final não encontrado: {result_file}. Nada a limpar.")
        return

    df = pd.read_csv(result_file)
    rows_before = len(df)

    # Descarta linhas sem Cluster ID (não fazem sentido no resultado final)
    if "Cluster ID" in df.columns:
        df = df.dropna(subset=["Cluster ID"])
        df["Cluster ID"] = df["Cluster ID"].astype(int)

    # Limpa NaN: numérico -> 0; texto -> string vazia (e remove "nan"/"None")
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        else:
            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .str.strip()
                .replace(list(EMPTY_TOKENS), "")
            )

    # Reordena colunas conforme a ordem preferida (mantém as extras ao final)
    ordered = [c for c in PREFERRED_ORDER if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    df = df[ordered + extras]

    # Reordena linhas por Cluster ID
    if "Cluster ID" in df.columns:
        df = df.sort_values("Cluster ID").reset_index(drop=True)

    df.to_csv(result_file, index=False)

    print(
        f"Limpeza final concluída: {len(df)} clusters "
        f"({rows_before - len(df)} linha(s) removida(s)), "
        f"{len(df.columns)} colunas reordenadas."
    )


if __name__ == "__main__":
    main()
