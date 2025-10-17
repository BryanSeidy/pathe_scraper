# ---------- csv_writer.py ----------
import os, csv
from datetime import datetime
import config


def write_csv(rows):
    if not rows:
        return None
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(config.OUTPUT_DIR, f'horaires_pathe_{ts}.csv')
    fieldnames = ["cinema_id", "cinema_name", "movie_id", "movie_title", "show_date", "start_time"]
    seen = set()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        f.write(";".join(fieldnames) + "\n")

        # 2) Writer pour les données (avec guillemets si nécessaire)
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        for row in rows:
            # Skip rows for unknown movies (no ID)
            if not row.get("movie_id"):
                continue
            # Extraire les valeurs dans l'ordre des colonnes
            writer.writerow([
                row.get("cinema_id", ""),
                row.get("cinema_name", ""),
                row.get("movie_id", ""),
                row.get("movie_title", ""),
                row.get("show_date", ""),
                row.get("start_time", ""),
            ])

    return filename


def write_csv_to_path(rows, dest_path: str):
    if not rows or not dest_path:
        return None
    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dest_path) or '.', exist_ok=True)
    fieldnames = ["cinema_id", "cinema_name", "movie_id", "movie_title", "show_date", "start_time"]
    with open(dest_path, 'w', newline='', encoding='utf-8') as f:
        f.write(";".join(fieldnames) + "\n")
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            # Skip rows for unknown movies (no ID)
            if not row.get("movie_id"):
                continue
            writer.writerow([
                row.get("cinema_id", ""),
                row.get("cinema_name", ""),
                row.get("movie_id", ""),
                row.get("movie_title", ""),
                row.get("show_date", ""),
                row.get("start_time", ""),
            ])
    return dest_path


def generate_csv_filename(cinema_name: str, selected_date: str, timestamp: str = None):
    """Generate CSV filename with format: show_times-NomDuCinema-DateSelectionner-AAAAMMJJ-HHMMSS"""
    from datetime import datetime
    
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    # Clean cinema name (remove special chars, replace spaces with underscores)
    clean_cinema = cinema_name.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '').replace("'", '')
    
    # Format selected date as Dim_12_Oct
    try:
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        day_names = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        month_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        day_name = day_names[date_obj.weekday()]
        month_name = month_names[date_obj.month - 1]
        formatted_date = f"{day_name}_{date_obj.day:02d}_{month_name}"
    except Exception:
        formatted_date = selected_date.replace('-', '_')
    
    return f"show_times-{clean_cinema}-{formatted_date}-{timestamp}.csv"