# ---------- scraper.py ----------
import time, logging, re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from driver_manager import build_driver, get_driver, quit_driver, ensure_driver_alive
import config
from cinema_matcher import get_cinema_id_for_config

TIME_REGEX = re.compile(r"(\d{1,2}[:h]\d{2})", re.IGNORECASE)


def normalize_time(t: str) -> str:
    return t.replace('h', ':').strip()


def scroll_to_bottom(driver, pause=2.5, max_attempts=12):
    """Perform a slower, more natural scroll with small increments and short pauses."""
    import random
    viewport_height = driver.execute_script("return window.innerHeight || document.documentElement.clientHeight || 800;")
    total_height = driver.execute_script("return document.body.scrollHeight")
    current_position = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop || 0;")
    attempts = 0
    steps_per_attempt = 8  # number of small steps before checking for new content
    while attempts < max_attempts:
        steps = 0
        while steps < steps_per_attempt:
            # Natural small increment (20% to 40% of viewport)
            delta = int(viewport_height * random.uniform(0.20, 0.40))
            current_position += delta
            driver.execute_script("window.scrollTo(0, arguments[0]);", current_position)
            # Natural pause between steps with slight jitter
            time.sleep(random.uniform(0.45, 0.85))
            steps += 1
        # After a batch of steps, give more time for lazy content
        time.sleep(max(0.6, pause - 1.5) if pause > 1.5 else 0.6)
        new_total = driver.execute_script("return document.body.scrollHeight")
        # If near the bottom and page height didn't increase, count an attempt
        if new_total <= total_height + 10 and (current_position + viewport_height >= new_total - 5):
            attempts += 1
        else:
            attempts = 0  # reset attempts if new content appeared
        total_height = max(total_height, new_total)
        if current_position + viewport_height >= total_height - 2:
            # final small settle wait to allow any last lazy items
            time.sleep(1.0)
            break
    logging.info("Smooth scroll completed (attempt windows exhausted or bottom reached).")


def scroll_back_to_top(driver, pause=2.0):
    """Perform a slow, natural scroll back to the top after reaching bottom."""
    import random
    viewport_height = driver.execute_script("return window.innerHeight || document.documentElement.clientHeight || 800;")
    current_position = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop || 0;")
    steps_per_batch = 8
    while current_position > 0:
        for _ in range(steps_per_batch):
            # Natural small decrement (20% to 35% of viewport)
            delta = int(viewport_height * random.uniform(0.20, 0.35))
            current_position = max(0, current_position - delta)
            driver.execute_script("window.scrollTo(0, arguments[0]);", current_position)
            time.sleep(random.uniform(0.45, 0.85))
            if current_position <= 0:
                break
        time.sleep(max(0.5, pause - 1.2) if pause > 1.2 else 0.5)
    # Ensure at absolute top and settle
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.8)


def accept_cookies(driver):
    try:
        # Single quick attempt; if not found quickly, proceed without blocking the flow
        WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.ID, config.COOKIE_BTN_ID)))
        btn = driver.find_element(By.ID, config.COOKIE_BTN_ID)
        driver.execute_script("arguments[0].click();", btn)
        logging.info("Cookies accepted via Didomi button.")
    except TimeoutException:
        logging.info("No cookie popup found quickly; continuing.")
    except Exception:
        logging.exception("Exception while trying to accept cookies; proceeding anyway.")


def close_announcement_if_any(driver, attempts: int = 3):
    """Close Majestic announcement popup if present. Tries robust strategies.
    Targets both generic class selector and the specific #dialog7 > button path.
    """
    selectors = [
        '#dialog7 > button.eb-close.placement-inside',
        '#dialog7 > button',
        'button.eb-close.placement-inside',
    ]
    for _ in range(attempts):
        try:
            for sel in selectors:
                try:
                    el = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                except Exception:
                    el = None
                if not el:
                    continue
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                except Exception:
                    pass
                # Try JS click first
                try:
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.2)
                    return
                except Exception:
                    pass
                # Fallback: normal click if clickable
                try:
                    WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                    el.click()
                    time.sleep(0.2)
                    return
                except Exception:
                    pass
        except Exception:
            pass
        # small pause before next attempt
        time.sleep(0.3)

def click_cinema_link(driver, selector):
    WebDriverWait(driver, config.TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    link = driver.find_element(By.CSS_SELECTOR, selector)
    driver.execute_script("arguments[0].click();", link)
    
    logging.info("Clicked cinema link: %s", selector)
    # give the page time to begin loading
    time.sleep(2)


def parse_duration(duration):
    if not duration:
        return None
    text = duration.strip()
    pattern = re.search(r"(\d+)h(?:\s*(\d+))?", text)
    if pattern:
        hours = int(pattern.group(1))
        minutes = int(pattern.group(2)) if pattern.group(2) else 0
        return hours * 60 + minutes
    else:
        pattern = re.search(r"(\d+)\s*min", text)
        if pattern:
            return int(pattern.group(1))
    return None


def _retry(operation, attempts=3, delay=0.6, backoff=1.7, exceptions=(Exception,)):
    """Generic retry helper with exponential backoff."""
    tries = 0
    wait = delay
    while True:
        try:
            return operation()
        except exceptions as e:
            tries += 1
            if tries >= attempts:
                raise
            time.sleep(wait)
            wait *= backoff


def _format_majestic_date(parts: list[str]) -> str:
    """Convert Majestic date parts (e.g., ['Mar', '21', 'Oct']) to YYYY-MM-DD.
    Assumes current year if none is provided.
    """
    try:
        from datetime import datetime
        # Normalize parts: ignore weekday labels if present, keep numeric day and month label
        clean = [p.strip() for p in parts if p and p.strip()]
        # Find day (first integer in parts)
        day = None
        month_label = None
        for p in clean:
            if p.isdigit():
                day = int(p)
                continue
            # candidate month label
            if month_label is None:
                month_label = p
        if day is None or not month_label:
            return datetime.today().strftime('%Y-%m-%d')
        # French month mappings (short labels)
        month_map = {
            'jan': 1, 'janv': 1, 'jan.': 1, 'janvier': 1,
            'fév': 2, 'fev': 2, 'fév.': 2, 'février': 2,
            'mar': 3, 'mar.': 3, 'mars': 3,
            'avr': 4, 'avr.': 4, 'avril': 4,
            'mai': 5,
            'jun': 6, 'juin': 6, 'juin.': 6,
            'jul': 7, 'juil': 7, 'juil.': 7, 'juillet': 7,
            'aoû': 8, 'aou': 8, 'août': 8, 'août.': 8,
            'sep': 9, 'sept': 9, 'sept.': 9, 'septembre': 9,
            'oct': 10, 'oct.': 10, 'octobre': 10,
            'nov': 11, 'nov.': 11, 'novembre': 11,
            'déc': 12, 'dec': 12, 'déc.': 12, 'décembre': 12,
        }
        key = month_label.lower().replace('é', 'e').replace('û', 'u').replace('ô', 'o').replace('à', 'a').replace('ï', 'i')
        key = key.replace('é', 'e')  # ensure accents removed
        # Also strip trailing dots/spaces
        key = key.strip('. ')
        month = month_map.get(key, None)
        if not month:
            # Try first three letters
            month = month_map.get(key[:3], None)
        if not month:
            return datetime.today().strftime('%Y-%m-%d')
        year = datetime.today().year
        # Zero-pad
        return f"{year:04d}-{month:02d}-{day:02d}"
    except Exception:
        from datetime import datetime
        return datetime.today().strftime('%Y-%m-%d')

def extract_showtimes(headless: bool = False, cinema_key: str = 'ci_cap_sud', selected_date: str | None = None, is_today: bool = True):
    """Main orchestrator: returns list of dict rows.
    Each row: cinema_id, cinema_name, movie_title, show_date, start_time
    """
    driver = ensure_driver_alive(headless=headless)
    if driver is None:
        logging.error("Driver could not be initialized. Exiting extract_showtimes.")
        return []
    rows = []
    try:
        # Resolve cinema-specific settings
        cinema = config.CINEMAS.get(cinema_key, config.CINEMAS['ci_cap_sud'])
        base_url = cinema.get('base_url', config.BASE_URL)
        cinema_url = cinema.get('cinema_url')
        cinema_link_selector = cinema.get('cinema_link_selector', config.CINEMA_LINK_SELECTOR)
        secondary_cinema_link_selector = cinema.get('secondary_cinema_link_selector')
        movie_card_selector = cinema.get('movie_card_selector', config.MOVIE_CARD_SELECTOR)
        movie_title_selector = cinema.get('movie_title_selector', config.MOVIE_TITLE_SELECTOR)
        hour_selector = cinema.get('hour_selector', config.HOUR_SELECTOR)
        duration_selector = cinema.get('duration_selector', config.DURATION_SELECTOR)
        # Get cinema ID from database matching
        cinema_id = get_cinema_id_for_config(cinema_key)
        if cinema_id is None:
            cinema_id = cinema.get('cinema_id', config.CINEMA_ID)
        cinema_name = cinema.get('cinema_name', config.CINEMA_NAME)

        target_date = selected_date or datetime.today().strftime('%Y-%m-%d')
        # Support quick re-scrape mode via config flag to skip initial navigation
        quick = getattr(config, 'QUICK_RESCRAPE', False)
        if not quick:
            if cinema.get('site') == 'majestic':
                logging.info("Majestic navigation start: %s", base_url)
                driver.get(base_url)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                close_announcement_if_any(driver)
                try:
                    salle_selector = cinema.get('majestic_salle_selector')
                    item_selector = cinema.get('majestic_cinema_item_selector')
                    if salle_selector and item_selector:
                        from selenium.webdriver.common.action_chains import ActionChains
                        salle = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, salle_selector)))
                        ActionChains(driver).move_to_element(salle).perform()
                        time.sleep(0.5)
                        item = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, item_selector)))
                        driver.execute_script("arguments[0].click();", item)
                        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                        time.sleep(1.0)
                        close_announcement_if_any(driver)
                except Exception:
                    logging.exception('Majestic header navigation failed; continuing')
            else:
                logging.info("Loading base and navigating: %s", base_url)
                driver.get(base_url)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                time.sleep(2.0)
                accept_cookies(driver)
                _retry(lambda: click_cinema_link(driver, cinema_link_selector), attempts=1, delay=0.8, backoff=1.5, exceptions=(TimeoutException, Exception))
                # For Morocco request: click secondary Pathé Californie link if provided
                if secondary_cinema_link_selector:
                    try:
                        _retry(lambda: click_cinema_link(driver, secondary_cinema_link_selector), attempts=2, delay=0.4, backoff=1.5, exceptions=(TimeoutException, Exception))
                    except Exception:
                        logging.exception("Secondary cinema link click failed; continuing anyway.")
        else:
            logging.info("Quick re-scrape enabled: skipping cookies and cinema navigation")

        # Date slider navigation applies only to Pathé sites
        if cinema.get('site') != 'majestic':
            try:
                base_date = datetime.today().date()
                offset_days = 0
                if selected_date:
                    try:
                        sd = datetime.strptime(selected_date, '%Y-%m-%d').date()
                        offset_days = (sd - base_date).days
                    except Exception:
                        offset_days = 0
                if offset_days >= 1:
                    if offset_days == 1:
                        slider_selector = "#toBarDatePicker > div > cgp-calendar > div.tw-relative.tw-w-full.tw-h-full.tw-overflow-hidden.max-lg\\:tw-slider-mobile-size.max-lg\\:-tw-ml-2.lg\\:tw-px-8 > div.tw-relative.tw-w-full.tw-h-full.tw-mask-left > div > swiper > div > div.tw-swiper-slide.swiper-slide-next > a"
                    else:
                        index = min(6, max(3, 1 + offset_days))
                        slider_selector = f"#toBarDatePicker > div > cgp-calendar > div.tw-relative.tw-w-full.tw-h-full.tw-overflow-hidden.max-lg\\:tw-slider-mobile-size.max-lg\\:-tw-ml-2.lg\\:tw-px-8 > div.tw-relative.tw-w-full.tw-h-full.tw-mask-left > div > swiper > div > div:nth-child({index}) > a"
                    _retry(lambda: click_cinema_link(driver, slider_selector), attempts=3, delay=0.8, backoff=1.5, exceptions=(TimeoutException, Exception))
                    time.sleep(2.0)
            except Exception:
                logging.exception("Date slider navigation failed; continuing anyway.")

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(2.0)

        if cinema.get('site') == 'majestic':
            try:
                cards = WebDriverWait(driver, 12).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.AUgnqrUu')))
            except TimeoutException:
                cards = []
            logging.info('Majestic: found %d movie cards', len(cards))
            for card in cards:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", card)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h2.W2nsCKpB')))
                    close_announcement_if_any(driver)
                    movie_title = driver.find_element(By.CSS_SELECTOR, 'h2.W2nsCKpB').text.strip()
                    # duration
                    duration_minutes = None
                    try:
                        dur_el = driver.find_element(By.CSS_SELECTOR, 'span.DAna1liq')
                        duration_minutes = parse_duration(dur_el.text)
                    except Exception:
                        duration_minutes = None
                    # Tabs per day
                    tabs = driver.find_elements(By.CSS_SELECTOR, "div.ant-tabs-tab[role='tab']")
                    for t in tabs:
                        try:
                            driver.execute_script("arguments[0].click();", t)
                            try:
                                WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.enWqIGWP')))
                            except TimeoutException:
                                continue
                            # show date parts
                            try:
                                parts = [c.text.strip() for c in driver.find_element(By.CSS_SELECTOR, 'div.GPEjpDjV').find_elements(By.CSS_SELECTOR, 'div') if c.text.strip()]
                                show_date = _format_majestic_date(parts) if parts else datetime.today().strftime('%Y-%m-%d')
                            except Exception:
                                show_date = datetime.today().strftime('%Y-%m-%d')
                            for sp in driver.find_elements(By.CSS_SELECTOR, 'span.underline'):
                                time_str = normalize_time(sp.text.strip())
                                rows.append({
                                    'cinema_id': cinema_id,
                                    'cinema_name': cinema_name,
                                    'movie_title': movie_title,
                                    'show_date': show_date,
                                    'start_time': time_str,
                                    'duration': duration_minutes
                                })
                        except Exception:
                            logging.exception('Majestic tab parsing failed; continuing')
                    # back
                    try:
                        back_btn = driver.find_element(By.CSS_SELECTOR, 'button.EP_xg_rA')
                        driver.execute_script("arguments[0].click();", back_btn)
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.AUgnqrUu')))
                        close_announcement_if_any(driver)
                    except Exception:
                        logging.exception('Majestic back failed; using browser back')
                        driver.back(); time.sleep(1.0)
                except Exception:
                    logging.exception('Majestic movie detail parse failed; skipping card')
            logging.info('Total showtime rows extracted (Majestic): %d', len(rows))
            return rows
        else:
            # wait for movie cards to appear; retry a few times if necessary
            found_cards = False
            for _ in range(4):
                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, movie_card_selector)))
                    found_cards = True
                    break
                except TimeoutException:
                    logging.info("Waiting for movie cards to render...")
                    time.sleep(3)
            if not found_cards:
                logging.warning("Movie cards did not render within expected time.")

        # scroll progressively to load everything, then back to top as requested
        scroll_to_bottom(driver, pause=2.5, max_attempts=12)
        scroll_back_to_top(driver, pause=2.0)
        movie_cards = driver.find_elements(By.CSS_SELECTOR, movie_card_selector)
        logging.info("Found %d movie card elements.", len(movie_cards))

        for card in movie_cards:
            try:
                # retry finding the title within the card, keeping CSS selector unchanged
                title_el = _retry(
                    lambda: card.find_element(By.CSS_SELECTOR, movie_title_selector),
                    attempts=3,
                    delay=0.5,
                    backoff=1.6,
                    exceptions=(NoSuchElementException,)
                )
                movie_title = title_el.text.strip() if title_el else ''
                if not movie_title:
                    continue
                # duration: try within card else global
                duration = ''
                duration_minutes = None
                try:
                    try:
                        d_el = card.find_element(By.CSS_SELECTOR, duration_selector)
                    except Exception:
                        d_elems = driver.find_elements(By.CSS_SELECTOR, duration_selector) if driver else []
                        d_el = d_elems[1] if d_elems else None
                    if d_el:
                        duration = d_el.text.strip()
                        duration_minutes = parse_duration(duration)
                        logging.info(f"Duration: {duration_minutes} minutes")
                except Exception:
                    duration = ''
                    duration_minutes = None
                hour_els = card.find_elements(By.CSS_SELECTOR, hour_selector)
                for h in hour_els:
                    raw = h.text.strip()
                    if not raw:
                        continue
                    m = TIME_REGEX.search(raw)
                    time_str = normalize_time(m.group(1)) if m else raw
                    rows.append({
                        'cinema_id': cinema_id,
                        'cinema_name': cinema_name,
                        'movie_title': movie_title,
                        'show_date': target_date,
                        'start_time': time_str,
                        'duration': duration_minutes
                    })
            except Exception:
                logging.exception('Error parsing a movie card; skipping it.')
                continue

        logging.info('Total showtime rows extracted: %d', len(rows))
        return rows

    finally:
        # do not quit here to allow manual closing via GUI; caller may call quit_driver()
        logging.info('Scraping step finished; driver still running for manual control until closed.')
