import pandas as pd
import tqdm

def count_words(text):
    if not isinstance(text, str):
        return 0
    return len(text.split())

def clean_dataframe(df, config):

    lower_word_limit = config["word_limit"]["lower"]
    upper_word_limit = config["word_limit"]["upper"]
    year_cutoff = config["cutoff"]["year_cutoff"]

    print(type(year_cutoff))
    print(year_cutoff)

    df = df.dropna(subset=['canonical_url', 'title', 'text'])
    df = df[df['text'].str.strip() != ""]

    #df['publish_date'] = pd.to_datetime(df['publish_date'], errors='coerce')
    #df = df[df['publish_date'].notnull()]
    #df['year'] = df['publish_date'].dt.year

    #df = df[df['year'] <= year_cutoff]

    df['word_count'] = df['text'].apply(count_words)

    df = df[
        (df['word_count'] >= lower_word_limit) &
        (df['word_count'] <= upper_word_limit)
    ]

    df = df.drop_duplicates(subset=['canonical_url'])
    df = df.drop_duplicates(subset=['title', 'publish_date'])

    return df.reset_index(drop=True)

def concatenate_files(files):
    """
    Concatenate the files using pandas.concat.
    
    Parameters:
    - files: list
    
    Returns:
    - df: pandas.DataFrame
    """
    dfs = []
    for file in tqdm.tqdm(files):
        df = pd.read_csv(file)
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    return df

def sort_dataframe(df):
    """
    Sort the dataframe by the 'Year' and then by 'Journal' within each year.

    Parameters:
    - df: pandas.DataFrame

    Returns:
    - df: pandas.DataFrame
    """

    df = df.sort_values(by=['publish_date', 'source'])
    return df