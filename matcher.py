# ---------- matcher.py ----------
import os, pandas as pd, logging
from datetime import date, datetime
from difflib import get_close_matches
import config


def ensure_db_exists():
    os.makedirs(os.path.dirname(config.EXCEL_DB), exist_ok=True)
    if not os.path.exists(config.EXCEL_DB):
        # initial file with expected headers
        df = pd.DataFrame(columns=[
            "ID",
            "Original title",
            "Title",
            "Duration",
            "Release date",
            "Created at",
        ])
        df.to_excel(config.EXCEL_DB, index=False, engine='openpyxl')
        logging.info('Created new Excel DB at %s', config.EXCEL_DB)


def load_db():
    ensure_db_exists()
    df = pd.read_excel(config.EXCEL_DB, engine='openpyxl')
    # ensure required columns exist
    for col in ['Original title', 'Title', 'Duration', 'Release date', 'Created at']:
        if col not in df.columns:
            df[col] = ''
    # normalize both title columns for matching
    df['Name_norm_original'] = df['Original title'].astype(str).str.strip().str.lower()
    df['Name_norm_title'] = df['Title'].astype(str).str.strip().str.lower()
    if 'ID' not in df.columns:
        df['ID'] = pd.Series(dtype='int64')
    return df


def persist_db(df):
    df_to_save = df.drop(columns=['Name_norm', 'Name_norm_original', 'Name_norm_title'], errors='ignore')
    df_to_save.to_excel(config.EXCEL_DB, index=False, engine='openpyxl')
    logging.info('Excel DB saved to %s', config.EXCEL_DB)


def match_movie_ids(rows: list) -> list:
    """For each row dict, attach 'movie_id'. Update DB when unknown.
    Returns modified rows list.
    """
    df = load_db()
    # Build combined lookup from both name fields
    existing_names = []
    name_to_id = {}
    for idx, row in df.iterrows():
        for key in (row.get('Name_norm_original', ''), row.get('Name_norm_title', '')):
            k = str(key) if pd.notna(key) else ''
            if not k:
                continue
            existing_names.append(k)
            # do not overwrite existing mapping; first non-empty wins
            name_to_id.setdefault(k, int(row['ID']) if pd.notna(row.get('ID')) else None)
    # No auto-assignment for new movies: we will flag unknowns and not persist
    # ensure ID column numeric
    # if 'ID' not in df.columns or df['ID'].isnull().all():
    #     df['ID'] = pd.Series(dtype=int)

    for r in rows:
        title = r['movie_title'].strip()
        tn = title.lower()
        r['movie_id'] = None

        # exact match on either column
        matches = df[(df['Name_norm_original'] == tn) | (df['Name_norm_title'] == tn)]
        if not matches.empty:
            r['movie_id'] = int(matches.iloc[0]['ID'])
            continue

        # fuzzy fallback
        close = get_close_matches(tn, existing_names, n=1, cutoff=0.85)
        if close:
            # map back to ID using combined dict
            mapped_id = name_to_id.get(close[0])
            if mapped_id is not None and not pd.isna(mapped_id):
                r['movie_id'] = int(mapped_id)
                continue

        # not found -> mark as unknown; do not add to DB and do not assign ID
        r['movie_id'] = None
        r['unknown_movie'] = True
        logging.info('⚠️ Nouveau film non présent dans la BD: %s', title)

    # We intentionally do NOT persist DB changes here; unknowns are not added automatically
    return rows
