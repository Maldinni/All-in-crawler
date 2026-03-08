import re
import unicodedata

import pandas as pd
import tqdm

def count_words(text):
    if not isinstance(text, str):
        return 0
    return len(text.split())

def truncate_text(text, max_words=250):
    """
    Limita o texto a no máximo max_words palavras.
    """
    if not isinstance(text, str):
        return text

    words = text.split()
    if len(words) <= max_words:
        return text
    else:
        return " ".join(words[:max_words])

def remove_emojis(text):
    if not isinstance(text, str):
        return text

    # Remove emojis por categoria Unicode
    return ''.join(
        char for char in text
        if not (
            unicodedata.category(char) in ['So', 'Sk'] and
            ('EMOJI' in unicodedata.name(char, '') or
             ord(char) > 10000)
        )
    )

def clean_dataframe(df, config):

    lower_word_limit = config["word_limit"]["lower"]
    upper_word_limit = config["word_limit"]["upper"]
    year_cutoff = config["cutoff"]["year_cutoff"]

    print(type(year_cutoff))
    print(year_cutoff)

    df = df.dropna(subset=['canonical_url', 'title', 'text'])
    df = df[df['text'].str.strip() != ""]

    df['text'] = df['text'].apply(remove_emojis)
    df['text'] = df['text'].apply(lambda x: truncate_text(x, max_words=250))
    df['title'] = df['title'].apply(remove_emojis)
    df['authors'] = df['authors'].apply(remove_emojis)

    # Agora a contagem de palavras vai considerar no máximo 250
    df['word_count'] = df['text'].apply(count_words)

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
    - df: pandas.DataFramea
    """

    df = df.sort_values(by=['publish_date', 'source'])
    return df