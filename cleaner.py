import glob
import os

from src.utils.cleaning import clean_dataframe, concatenate_files, sort_dataframe
from src.utils.parsing import parse_args, load_config
from src.utils.io import ensure_dirs

def main():
    args = parse_args()
    cfg = load_config(args)

    paths = cfg["paths"]
    ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

    raw_directory = f'{cfg["paths"]["raw"]}'
    cleaned_directory = f'{cfg["paths"]["processed"]}'

    raw_files = glob.glob(os.path.join(raw_directory, '*.csv'))

    print(f'Merging {len(raw_files)} files.')
    df = concatenate_files(raw_files)        # Combines all CSVs into a single DataFrame

    print(f'Cleaning the merged dataframe with {len(df)} articles.')
    df = clean_dataframe(df, cfg)        # Removes duplicates, filters by word count and year, and cleans text

    print(f'Number of articles after cleaning: {len(df)}')

    # --- Sort and save the cleaned DataFrame ---
    print('Sorting the clean dataframe.')
    df = sort_dataframe(df)                  # Sorts articles, typically by publication date or ID

    print(f'Saving the clean dataframe to {cleaned_directory}.')
    os.makedirs(cleaned_directory, exist_ok=True)  # Creates output directory if it does not exist

    # Save the final cleaned dataset to CSV format
    df.to_csv(
        os.path.join(cleaned_directory, 'articles_merged_cleaned.csv'),
        index=False
    )

if __name__ == "__main__":
    main()
