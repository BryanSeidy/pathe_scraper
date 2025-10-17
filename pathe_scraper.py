# ---------- main.py ----------
import argparse
import logging
import os
from scraper import extract_showtimes
from matcher import match_movie_ids
from csv_writer import write_csv
from tkinter import messagebox
from driver_manager import quit_driver, ensure_driver_alive
import config
import gui


def setup_logging():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    logging.basicConfig(
        filename=config.LOG_FILE,
        filemode='a',
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S',
        level=logging.INFO
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pathe showtime scraper')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (default is visible)')
    args = parser.parse_args()

    setup_logging()
    logging.info('Starting scraper (headless=%s)', args.headless)

    # Defer scraping until user clicks from GUI home screen
    rows = []
    # final = start_gui(rows)


    # write CSV with timestamp
    csv_path = None

    # Track best (max) showtimes count per (cinema_key, date)
    best_counts: dict[tuple[str, str], int] = {}
    # Track cumulative showtimes extracted since app start
    cumulative_total_showtimes = 0

    def get_counts():
        return len(set(r['movie_title'] for r in rows)), len(rows)

    def on_scrape(selected_cinema_key: str, selected_date: str, is_today: bool):
        global rows
        try:
            # Clear previous data for fresh scraping session
            rows.clear()
            # ensure we have a live driver before refreshing
            ensure_driver_alive(headless=args.headless)
            new_rows = extract_showtimes(headless=args.headless, cinema_key=selected_cinema_key, selected_date=selected_date, is_today=is_today)
            if new_rows:
                new_rows = match_movie_ids(new_rows)
                # Build list of movies to add (unknowns with no ID)
                unknowns = {}
                for r in new_rows:
                    if not r.get('movie_id'):
                        key = (r.get('movie_title','').strip(), r.get('duration'))
                        unknowns[key] = {'title': key[0], 'duration': key[1]}
                # Write unknown movies to text file
                if unknowns:
                    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
                    txt_path = os.path.join(config.OUTPUT_DIR, 'movies_to_add.txt')
                    try:
                        # Load existing lines to avoid duplicates
                        existing = set()
                        if os.path.exists(txt_path):
                            try:
                                with open(txt_path, 'r', encoding='utf-8') as rf:
                                    for line in rf:
                                        line = line.strip()
                                        if line:
                                            existing.add(line)
                            except Exception:
                                logging.exception('Failed reading existing movies_to_add.txt; proceeding without dedupe baseline')
                        to_write = []
                        for (_title, _dur), _ in unknowns.items():
                            dur_str = '' if _dur is None else str(_dur)
                            line = f'movie_title : "{_title}", duration : "{dur_str}";'
                            if line not in existing:
                                to_write.append(line)
                        if to_write:
                            with open(txt_path, 'a', encoding='utf-8') as tf:
                                for l in to_write:
                                    tf.write(l + '\n')
                            logging.info('Appended %d unknown movie(s) to %s', len(to_write), txt_path)
                        else:
                            logging.info('No new unknown movies to append (all already listed).')
                    except Exception:
                        logging.exception('Failed to append to movies_to_add.txt')
                # Filter out unknowns from rows used by GUI/CSV
                new_rows = [r for r in new_rows if r.get('movie_id')]
                # Alert in GUI if unknowns found
                try:
                    count_unknowns = len(unknowns)
                except Exception:
                    count_unknowns = 0
                if count_unknowns:
                    try:
                        message = f"{count_unknowns} nouveau(x) film(s) trouvé(s).\nVeuillez ajouter ces films à ICICINE et mettre à jour la BD movies.xlsx"
                        messagebox.showwarning('Alerte', message)
                    except Exception:
                        logging.warning('GUI alert failed for unknown movies')
                # Add all new rows (no deduping since we cleared previous data)
                rows.extend(new_rows)
                # Update cumulative total (count rows added this run)
                global cumulative_total_showtimes
                added_count = len(new_rows)
                cumulative_total_showtimes += added_count
                logging.info('Cumulative showtimes so far (app runtime): %d', cumulative_total_showtimes)
                # Compute unique showtimes count for this (cinema, date)
                key = (selected_cinema_key, selected_date)
                unique_showtimes = set((r['movie_title'], r['show_date'], r['start_time']) for r in rows if r.get('show_date') == selected_date)
                current_count = len(unique_showtimes)
                previous_best = best_counts.get(key, 0)
                if current_count > previous_best:
                    best_counts[key] = current_count
                    logging.info('Best showtimes updated for %s@%s: %d', selected_cinema_key, selected_date, current_count)
                else:
                    logging.info('Showtimes unchanged for %s@%s: best=%d, current=%d', selected_cinema_key, selected_date, previous_best, current_count)
        except Exception as e:
            logging.exception('Refresh failed: %s', e)
        # Return GUI counts based on best recorded for this key
        key = (selected_cinema_key, selected_date)
        best = best_counts.get(key, 0)
        # Films détectés approximés par titres uniques dans la date
        film_count = len(set(r['movie_title'] for r in rows if r.get('show_date') == selected_date))
        return film_count, best, cumulative_total_showtimes
    
    logging.info('GUI started (you can close the driver manually via the GUI button).')


    def close_action():
        global csv_path
        csv_path = write_csv(rows)
        if csv_path:
            logging.info(f'💾 CSV saved: {csv_path}')
        else:
            logging.warning('No CSV produced (no rows).')
        quit_driver()
        logging.info('Process finished.')

    # Run GUI in the main thread to avoid Tkinter threading issues
    gui.start_gui(on_scrape, close_action, cinemas=config.CINEMAS, inactivity=1000, get_rows=lambda: rows)

