# ---------- driver_manager.py ----------

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import logging


dr = None


def build_driver(headless: bool = False):

    global dr
    if dr is not None:
        return dr

    opts = Options()
    # visible by default; set headless True when requested
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    try:
        dr = webdriver.Chrome(options=opts)
    except WebDriverException as e:
        logging.error("WebDriver initialization failed: %s", e)
        raise
    return dr


def get_driver():
    return dr


def quit_driver():
    global dr
    if dr:
        try:
            dr.quit()
            logging.info("Driver closed.")
        except Exception as e:
            logging.exception(e)
        finally:
            dr = None


def is_driver_alive() -> bool:
    """Best-effort check that current driver session is usable."""
    global dr
    if dr is None:
        return False
    try:
        _ = dr.current_url  # simple no-op call that touches the session
        return True
    except Exception:
        return False


def ensure_driver_alive(headless: bool = False):
    """Return a live driver; recreate if the global one is gone."""
    global dr
    if is_driver_alive():
        return dr
    # try clean shutdown just in case
    try:
        if dr:
            dr.quit()
    except Exception:
        pass
    dr = None
    logging.info("Recreating WebDriver (headless=%s)", headless)
    return build_driver(headless=headless)