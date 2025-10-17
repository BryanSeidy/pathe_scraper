# ---------- cinema_matcher.py ----------
import os, pandas as pd, logging
from datetime import datetime
import config


def ensure_cinemas_db_exists():
    os.makedirs(os.path.dirname(config.CINEMAS_DB), exist_ok=True)
    if not os.path.exists(config.CINEMAS_DB):
        # create initial file with headers
        df = pd.DataFrame(columns=["ID", "Name", "City", "Created at", "Website"])
        df.to_excel(config.CINEMAS_DB, index=False, engine='openpyxl')
        logging.info('Created new Cinemas DB at %s', config.CINEMAS_DB)


def load_cinemas_db():
    ensure_cinemas_db_exists()
    df = pd.read_excel(config.CINEMAS_DB, engine='openpyxl')
    # ensure required columns exist
    for col in ['ID', 'Name', 'City', 'Created at', 'Website']:
        if col not in df.columns:
            df[col] = ''
    return df


def persist_cinemas_db(df):
    df.to_excel(config.CINEMAS_DB, index=False, engine='openpyxl')
    logging.info('Cinemas DB saved to %s', config.CINEMAS_DB)


def normalize_cinema_name(name):
    """Remove 'Cinéma' prefix and strip spaces for comparison"""
    if not name:
        return ''
    # Remove 'Cinéma' prefix (case insensitive)
    normalized = name.lower().strip()
    if normalized.startswith('cinéma '):
        normalized = normalized[7:]  # Remove 'cinéma '
    elif normalized.startswith('cinema '):
        normalized = normalized[7:]  # Remove 'cinema '
    return normalized.strip()


def match_cinema_id(cinema_config):
    """Match cinema config with database and return cinema_id.
    If not found, add to database with new ID.
    """
    df = load_cinemas_db()
    cinema_name = cinema_config.get('cinema_name', '')
    cinema_url = cinema_config.get('cinema_url', '')
    
    # Try to match by URL first
    if cinema_url:
        url_matches = df[df['Website'].astype(str).str.contains(cinema_url.split('/')[-1], case=False, na=False)]
        if not url_matches.empty:
            cinema_id = int(url_matches.iloc[0]['ID'])
            logging.info('Cinema matched by URL: %s -> ID %d', cinema_name, cinema_id)
            return cinema_id
    
    # Try to match by exact name
    name_matches = df[df['Name'].astype(str).str.strip().str.lower() == cinema_name.lower()]
    if not name_matches.empty:
        cinema_id = int(name_matches.iloc[0]['ID'])
        logging.info('Cinema matched by exact name: %s -> ID %d', cinema_name, cinema_id)
        return cinema_id
    
    # Try to match by normalized name (without 'Cinéma' prefix)
    normalized_name = normalize_cinema_name(cinema_name)
    if normalized_name:
        for idx, row in df.iterrows():
            db_name = normalize_cinema_name(str(row.get('Name', '')))
            if db_name and normalized_name == db_name:
                cinema_id = int(row['ID'])
                logging.info('Cinema matched by normalized name: %s -> ID %d', cinema_name, cinema_id)
                return cinema_id
    
    # Not found - add new cinema to database
    next_id = int(df['ID'].max()) + 1 if len(df) > 0 and not df['ID'].isnull().all() else 1
    new_row = {
        'ID': next_id,
        'Name': cinema_name,
        'City': cinema_config.get('country', ''),
        'Created at': datetime.today().strftime('%Y-%m-%d %H-%M-%S'),
        'Website': cinema_url
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    persist_cinemas_db(df)
    logging.info('New cinema added to DB: %s -> ID %d', cinema_name, next_id)
    return next_id


def get_cinema_id_for_config(cinema_key):
    """Get cinema ID for a given cinema key from config"""
    cinema_config = config.CINEMAS.get(cinema_key)
    if not cinema_config:
        logging.warning('Cinema key not found: %s', cinema_key)
        return None
    return match_cinema_id(cinema_config)

