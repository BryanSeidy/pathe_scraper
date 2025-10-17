# ---------- config.py ----------
BASE_URL = "https://www.pathe.ci/fr/cinemas"
CINEMA_ID = 14
CINEMA_NAME = "Cinéma"
CINEMA_LINK_SELECTOR = "nav ul li:nth-child(2) a[href*='cinema-pathe-cap-sud']"
MOVIE_CARD_SELECTOR = "div.tw-group"
MOVIE_TITLE_SELECTOR = "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span"
HOUR_SELECTOR = "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary"
DURATION_SELECTOR = "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)"
COOKIE_BTN_ID = "didomi-notice-agree-button"


OUTPUT_DIR = "output"
EXCEL_DB = "databases/movies.xlsx" # must exist; columns: ID, Original title, Duration, Release date
CINEMAS_DB = "databases/cinemas.xlsx" # must exist; columns: ID, Name, City, Created at, Website
LOG_FILE = OUTPUT_DIR + "/scrap.log"
TIMEOUT = 45
QUICK_RESCRAPE = False

# Site mapping to support country selection and direct cinema URLs
# Keys are short codes for internal use; 'label' is what the user sees in the GUI
CINEMAS = {
    'ci_cap_sud': {
        'label': "Cinéma Pathé Cap Sud",
        'country': "Côte d'Ivoire",
        'base_url': "https://www.pathe.ci/fr/cinemas",
        'cinema_url': "https://www.pathe.ci/fr/cinemas/cinema-pathe-cap-sud",
        'cinema_id': 14,
        'cinema_name': "Cinéma Pathé Cap Sud",
        'cinema_link_selector': "nav ul li:nth-child(2) a[href*='cinema-pathe-cap-sud']",
        'movie_card_selector': "div.tw-group",
        'movie_title_selector': "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span",
        'hour_selector': "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary",
        'duration_selector': "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)",
    },
    'sn_dakar': {
        'label': "Cinéma Pathé Dakar",
        'country': "Sénégal",
        'base_url': "https://www.pathe.sn/fr/cinemas",
        'cinema_url': "https://www.pathe.sn/fr/cinemas/cinema-pathe-dakar",
        'cinema_id': 201,
        'cinema_name': "Cinéma Pathé Dakar",
        'cinema_link_selector': "a[href*='cinema-pathe-dakar']",
        'movie_card_selector': "div.tw-group",
        'movie_title_selector': "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span",
        'hour_selector': "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary",
        'duration_selector': "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)",
    },
    'be_charleroi': {
        'label': "Cinéma Pathé Charleroi",
        'country': "Belgique",
        'base_url': "https://www.pathe.be/fr/cinemas",
        'cinema_url': "https://www.pathe.be/fr/cinemas/cinema-pathe-charleroi",
        'cinema_id': 301,
        'cinema_name': "Cinéma Pathé Charleroi",
        'cinema_link_selector': "a[href*='cinema-pathe-charleroi']",
        'movie_card_selector': "div.tw-group",
        'movie_title_selector': "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span",
        'hour_selector': "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary",
        'duration_selector': "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)",
    },
    'ma_casablanca': {
        'label': "Cinéma Pathé Californie Casablanca",
        'country': "Maroc",
        'base_url': "https://www.pathe.ma/fr/cinemas",
        'cinema_url': "https://www.pathe.ma/fr/cinemas/cinema-pathe-californie-casablanca",
        'cinema_id': 401,
        'cinema_name': "Cinéma Pathé Californie Casablanca",
        'cinema_link_selector': "a[href*='cinema-pathe-californie']",
        # After loading the country cinemas page, click the generic cinema link,
        # then specifically click the 'Pathé Californie' link in the accordion list
        # as requested: body > cgp-root > main > cgp-cinemas-page > ... > li > a
        'secondary_cinema_link_selector': "body > cgp-root > main > cgp-cinemas-page > section > div > div > div > cgp-empty-location > cgp-cinemas-list > div > div > div.accordion-panel > ul > li > a[href='/fr/cinemas/cinema-pathe-californie']",
        'movie_card_selector': "div.tw-group",
        'movie_title_selector': "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span",
        'hour_selector': "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary",
        'duration_selector': "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)",
    },
    'tn_tunis_city': {
        'label': "Cinéma Pathé Tunis City",
        'country': "Tunisie",
        'base_url': "https://www.pathe.tn/fr/cinemas",
        'cinema_url': "https://www.pathe.tn/fr/cinemas/cinema-pathe-tunis-city",
        'cinema_id': 501,
        'cinema_name': "Cinéma Pathé Tunis City",
        'cinema_link_selector': "body > cgp-root > main > cgp-cinemas-page > section > div > div > div > cgp-empty-location > cgp-cinemas-list > div > div > div.accordion-panel > ul > li:nth-child(1) > a",
        'movie_card_selector': "div.tw-group",
        'movie_title_selector': "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span",
        'hour_selector': "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary",
        'duration_selector': "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)",
    },
    'tn_azur_city': {
        'label': "Cinéma Pathé Azur City",
        'country': "Tunisie",
        'base_url': "https://www.pathe.tn/fr/cinemas",
        'cinema_url': "https://www.pathe.tn/fr/cinemas/cinema-pathe-azur-city",
        'cinema_id': 502,
        'cinema_name': "Cinéma Pathé Azur City",
        'cinema_link_selector': "body > cgp-root > main > cgp-cinemas-page > section > div > div > div > cgp-empty-location > cgp-cinemas-list > div > div > div.accordion-panel > ul > li:nth-child(2) > a",
        'movie_card_selector': "div.tw-group",
        'movie_title_selector': "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span",
        'hour_selector': "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary",
        'duration_selector': "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)",
    },
    'tn_mall_sousse': {
        'label': "Cinéma Pathé Mall Of Sousse",
        'country': "Tunisie",
        'base_url': "https://www.pathe.tn/fr/cinemas",
        'cinema_url': "https://www.pathe.tn/fr/cinemas/cinema-pathe-mall-of-sousse",
        'cinema_id': 503,
        'cinema_name': "Cinéma Pathé Mall Of Sousse",
        'cinema_link_selector': "body > cgp-root > main > cgp-cinemas-page > section > div > div > div > cgp-empty-location > cgp-cinemas-list > div > div > div.accordion-panel > ul > li:nth-child(3) > a",
        'movie_card_selector': "div.tw-group",
        'movie_title_selector': "h3.tw-items.tw-inline-block.tw-gap-1\\.5.tw-text-title-lg.tw-text-common-text-neutral-primary, span",
        'hour_selector': "div.tw-mb-0.tw-font-trade.tw-text-display-base.tw-text-common-text-neutral-primary",
        'duration_selector': "span.tw-mb-0.tw-flex.tw-gap-2.tw-text-regular-xs.tw-text-common-text-neutral-muted-placeholders span:nth-child(2)",
    },
    # Majestic cinemas (Côte d'Ivoire)
    'ci_maj_ivoire': {
        'label': "Majestic Cinéma Ivoire",
        'country': "Côte d'Ivoire",
        'base_url': "https://majesticcinema.ci/",
        'cinema_id': 601,
        'cinema_name': "Majestic Cinéma Ivoire",
        'site': 'majestic',
        'majestic_salle_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-navbar-container > div > nav > div.uk-navbar-right > ul > li.item-788.uk-parent",
        'majestic_cinema_item_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-drop.uk-navbar-dropdown.uk-open > div > ul > li.item-789",
    },
    'ci_maj_prima': {
        'label': "MAJESTIC PRIMA",
        'country': "Côte d'Ivoire",
        'base_url': "https://majesticcinema.ci/",
        'cinema_id': 602,
        'cinema_name': "MAJESTIC PRIMA",
        'site': 'majestic',
        'majestic_salle_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-navbar-container > div > nav > div.uk-navbar-right > ul > li.item-788.uk-parent",
        'majestic_cinema_item_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-drop.uk-navbar-dropdown.uk-open > div > ul > li.item-790",
    },
    'ci_maj_ficgayo': {
        'label': "Majestic Cinema Ficgayo",
        'country': "Côte d'Ivoire",
        'base_url': "https://majesticcinema.ci/",
        'cinema_id': 603,
        'cinema_name': "Majestic Cinema Ficgayo",
        'site': 'majestic',
        'majestic_salle_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-navbar-container > div > nav > div.uk-navbar-right > ul > li.item-788.uk-parent",
        'majestic_cinema_item_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-drop.uk-navbar-dropdown.uk-open > div > ul > li.item-792",
    },
    'ci_maj_sococe': {
        'label': "Majestic Cinéma Sococe",
        'country': "Côte d'Ivoire",
        'base_url': "https://majesticcinema.ci/",
        'cinema_id': 604,
        'cinema_name': "Majestic Cinéma Sococe",
        'site': 'majestic',
        'majestic_salle_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-navbar-container > div > nav > div.uk-navbar-right > ul > li.item-788.uk-parent",
        'majestic_cinema_item_selector': "body > div.tm-page > header.tm-header.uk-visible\\@m > div.uk-sticky > div.uk-drop.uk-navbar-dropdown.uk-open > div > ul > li.item-791",
    },
}