"""
GUI (gui.py)
"""

import tkinter as tk, threading, time
import subprocess, sys
from tkinter import ttk
from itertools import count
from driver_manager import quit_driver
import logging
import os
from PIL import Image, ImageTk
from tkinter import filedialog as fd
from csv_writer import write_csv_to_path
import config


def start_gui(on_scrape, on_close, cinemas: dict, inactivity=1000, get_rows=None):
    root = tk.Tk(); root.title('Pathé Scraper')

    # Theme management
    is_dark = True
    def get_theme_colors():
        if is_dark:
            return {
                'bg': '#0b0f17', 'fg': '#e6f1ff', 'accent': '#00e5ff', 'accent2': '#7c4dff',
                'button_bg': '#121826', 'entry_bg': '#1a1f2e', 'entry_fg': "#313131",
                'button_hover': '#1a2332', 'button_active': '#2a3441'
            }
        else:
            return {
                'bg': '#ffffff', 'fg': '#1a1f2e', 'accent': '#0066cc', 'accent2': '#4a90e2',
                'button_bg': '#f0f0f0', 'entry_bg': '#ffffff', 'entry_fg': '#1a1f2e',
                'button_hover': '#e0e0e0', 'button_active': '#d0d0d0'
            }

    def apply_theme():
        colors = get_theme_colors()
        root.configure(bg=colors['bg'])
        
        # Update all widgets
        for widget in root.winfo_children():
            update_widget_theme(widget, colors)
        
        # Update styles
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])
        style.configure('Header.TLabel', background=colors['bg'], foreground=colors['accent'], font=('Segoe UI', 16, 'bold'))
        style.configure('Count.TLabel', background=colors['bg'], foreground=colors['fg'], font=('Segoe UI', 11))
        style.configure('TButton', background=colors['button_bg'], foreground=colors['fg'], borderwidth=0, focusthickness=3, focuscolor=colors['accent'])
        style.map('TButton', background=[('active', colors['button_bg'])], foreground=[('active', colors['fg'])])
        style.configure('Accent.TButton', padding=8)
        style.configure('Purple.TButton', padding=8)
        style.configure('Horizontal.TProgressbar', troughcolor=colors['button_bg'], background=colors['accent2'], bordercolor=colors['bg'], lightcolor=colors['accent2'], darkcolor=colors['accent2'])
        style.configure('TCombobox', fieldbackground=colors['entry_bg'], background=colors['entry_bg'], foreground=colors['entry_fg'])

    def update_widget_theme(widget, colors):
        if isinstance(widget, tk.Frame):
            widget.configure(bg=colors['bg'])
        elif isinstance(widget, tk.Label):
            widget.configure(bg=colors['bg'], fg=colors['fg'])
        for child in widget.winfo_children():
            update_widget_theme(child, colors)

    # Initial theme
    apply_theme()

    # Header with responsive logo
    header_frame = tk.Frame(root, bg=get_theme_colors()['bg'])
    header_frame.pack(fill='x', pady=(12, 4))
    
    # Logo
    logo_path = os.path.join('assets', 'Scraper_logo.ico')
    original_logo_img = None
    logo_photo = None
    logo_label = tk.Label(header_frame, bg=get_theme_colors()['bg'])
    logo_label.pack(side='left', padx=(8, 10))
    
    header = ttk.Label(header_frame, text='Pathé Scraper', style='Header.TLabel')
    header.pack(side='left')
    
    # Theme toggle button with rounded style
    theme_btn = tk.Button(header_frame, text='🌙' if is_dark else '☀️', 
                        command=lambda: toggle_theme(), 
                        bg=get_theme_colors()['button_bg'], 
                        fg=get_theme_colors()['fg'],
                        relief='flat', bd=0, padx=12, pady=6,
                        font=('Segoe UI', 12), cursor='hand2')
    theme_btn.pack(side='right', padx=8)

    def toggle_theme():
        nonlocal is_dark
        is_dark = not is_dark
        apply_theme()
        theme_btn.configure(text='🌙' if is_dark else '☀️',
                            bg=get_theme_colors()['button_bg'],
                            fg=get_theme_colors()['fg'])
        # ensure logo background matches theme
        logo_label.configure(bg=get_theme_colors()['bg'])

    # Main controls frame
    controls = tk.Frame(root, bg=get_theme_colors()['bg'])
    controls.pack(pady=(8, 6), fill='x', padx=16)
    re_scrape_btn = None

    # Cinema dropdown
    ttk.Label(controls, text='Cinéma', style='TLabel').pack(anchor='w')
    cinema_var = tk.StringVar()
    cinema_keys = list(cinemas.keys())
    cinema_labels = [f"{cinemas[k]['label']} ({cinemas[k]['country']})" for k in cinema_keys]
    cinema_combo = ttk.Combobox(controls, values=cinema_labels, state='readonly', textvariable=cinema_var)
    cinema_combo.current(0)
    cinema_combo.pack(fill='x', pady=(2, 8))

    # Date dropdown (Aujourd'hui, Demain, +3 days) with French short labels
    from datetime import datetime, timedelta
    ttk.Label(controls, text='Date', style='TLabel').pack(anchor='w')
    date_var = tk.StringVar()
    def build_dates():
        today = datetime.today().date()
        day_names = ['Lun.', 'Mar.', 'Mer.', 'Jeu.', 'Ven.', 'Sam.', 'Dim.']
        month_names = ['jan.', 'fév.', 'mar.', 'avr.', 'mai', 'jun.', 'jui.', 'aoû.', 'sep.', 'oct.', 'nov.', 'déc.']
        labels = ["Aujourd'hui", "Demain"]
        values = [today.strftime('%Y-%m-%d'), (today + timedelta(days=1)).strftime('%Y-%m-%d')]
        for i in range(2, 6):
            d = today + timedelta(days=i)
            wd = d.weekday()  # 0=Mon .. 6=Sun
            # map Python weekday to our names (ensure wrap)
            wd_label = day_names[wd]
            mm_label = month_names[d.month - 1]
            label = f"{wd_label} {d.day:02d} {mm_label}"
            labels.append(label)
            values.append(d.strftime('%Y-%m-%d'))
        return labels, values
    date_labels, date_values = build_dates()
    date_combo = ttk.Combobox(controls, values=date_labels, state='readonly', textvariable=date_var)
    date_combo.current(0)
    date_combo.pack(fill='x', pady=(2, 8))

    # Status and counts
    status_var = tk.StringVar(value='Ready')
    status_lbl = ttk.Label(root, textvariable=status_var, style='Count.TLabel')
    status_lbl.pack(pady=(0, 4))

    # Dynamic counts (initially hidden)
    counts_frame = tk.Frame(root, bg=get_theme_colors()['bg'])
    counts_frame.pack(pady=(0, 8))
    
    lbl_f = ttk.Label(counts_frame, text='Films détectés: 0', style='Count.TLabel')
    lbl_h = ttk.Label(counts_frame, text='Horaires récupérés: 0', style='Count.TLabel')
    lbl_total = ttk.Label(counts_frame, text='Total showtimes (depuis ouverture): 0', style='Count.TLabel')
    
    # Initially hide counts
    lbl_f.pack_forget()
    lbl_h.pack_forget()

    # Animated GIF loader (deferred loading for fast startup)
    gif_path = os.path.join('assets', 'Scrape-Anime-Chargement.gif')
    gif_label = tk.Label(root, bg=get_theme_colors()['bg'])
    frames = []
    frame_index = 0
    animating = False

    # Progress bar (hidden when idle) above buttons
    pb = ttk.Progressbar(root, mode='indeterminate', length=320)
    pb.pack(pady=(2, 10))
    pb.pack_forget()

    last_action = time.time()

    def set_status(s):
        status_var.set(s)

    def update_counts(films, horaires, total=None):
        """Update count labels and show them"""
        lbl_f.config(text=f'Films détectés: {films}')
        lbl_h.config(text=f'Horaires récupérés: {horaires}')
        if total is not None:
            lbl_total.config(text=f'Total showtimes (depuis ouverture): {total}')
            lbl_total.pack(pady=(0, 4))
        lbl_f.pack(pady=(2, 2))
        lbl_h.pack(pady=(0, 8))

    def hide_counts_and_reset():
        try:
            lbl_f.config(text='Films détectés: 0')
            lbl_h.config(text='Horaires récupérés: 0')
            lbl_f.pack_forget()
            lbl_h.pack_forget()
        except Exception:
            pass

    def create_rounded_button(parent, text, command, style='primary'):
        """Create a rounded button with click effects"""
        colors = get_theme_colors()
        
        if style == 'primary':
            bg_color = colors['accent']
            hover_color = colors['accent2']
            fg_color = '#ffffff'
        elif style == 'danger':
            bg_color = '#d32f2f'
            hover_color = '#b71c1c'
            fg_color = '#ffffff'
        else:
            bg_color = colors['button_bg']
            hover_color = colors['button_hover']
            fg_color = colors['fg']
        
        btn = tk.Button(parent, text=text, command=command,
                        bg=bg_color, fg=fg_color, relief=tk.FLAT, bd=0,
                        padx=20, pady=10, font=('Segoe UI', 10, 'bold'),
                        cursor='hand2')
        
        def on_enter(e):
            btn.config(bg=hover_color)
        
        def on_leave(e):
            btn.config(bg=bg_color)
        
        def on_click(e):
            btn.config(bg=colors['button_active'])
            root.after(100, lambda: btn.config(bg=hover_color))
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.bind('<Button-1>', on_click)
        
        return btn

    def start_scraping():
        nonlocal last_action
        btn_start.config(state='disabled')
        pb.pack()
        pb.start(12)
        set_status('Loading')
        nonlocal animating
        # Hide dropdown controls and start button while scraping
        controls.pack_forget()
        try:
            btn_start.pack_forget()
        except Exception:
            pass
        # Hide any existing re-scrape button during the run
        nonlocal re_scrape_btn
        if re_scrape_btn is not None:
            try:
                re_scrape_btn.pack_forget()
            except Exception:
                pass

        def run_scrape():
            try:
                # resolve selections
                selected_cinema_key = cinema_keys[cinema_combo.current()]
                # date mapping
                idx = date_combo.current()
                today_selected = (idx == 0)
                selected_date = date_values[0] if today_selected else date_values[idx]
                f, h, tot = on_scrape(selected_cinema_key, selected_date, today_selected)
                root.after(0, lambda: update_counts(f, h, tot))
                root.after(0, lambda: set_status('Completed'))
            except Exception as e:
                logging.exception('Scraping failed: %s', e)
                root.after(0, lambda: set_status('Error'))
            finally:
                nonlocal animating
                animating = False
                # hide GIF and progress bar when scraping ends
                def hide_loading():
                    pb.stop(); pb.pack_forget(); gif_label.config(image='')
                    btn_start.config(state='normal')
                    # Show a Re-Scraper button; dropdowns remain hidden until clicked
                    nonlocal re_scrape_btn
                    def _show_controls_again():
                        if re_scrape_btn is not None:
                            re_scrape_btn.pack_forget()
                        # Restore dropdown controls to their original position above the start button
                        controls.pack(pady=(8, 6), fill='x', padx=16)
                        # Restore start button to its original position
                        try:
                            btn_start.pack(fill='x', pady=(0, 8))
                        except Exception:
                            pass
                        hide_counts_and_reset()
                    if re_scrape_btn is None:
                        re_scrape_btn = create_rounded_button(root, 'Re-Scraper', _show_controls_again, 'primary')
                    re_scrape_btn.pack(pady=(8, 6), fill='x', padx=16)
                    # Add a quick relaunch button under the dropdowns
                    try:
                        quick_row.pack_forget()
                    except Exception:
                        pass
                    quick_row.pack(pady=(0, 8), fill='x', padx=16)
                    # Show save buttons row after completion
                    try:
                        save_row.pack(fill='x', pady=(0, 8))
                    except Exception:
                        pass
                root.after(0, hide_loading)
                last_action = time.time()

        threading.Thread(target=run_scrape, daemon=True).start()

    def close_all():
        try:
            on_close()
        finally:
            nonlocal animating
            animating = False
            root.destroy()
            logging.info('GUI closed by user.')

    # Buttons frame (ensure progress bar is above by packing pb before this frame)
    btns = tk.Frame(root, bg=get_theme_colors()['bg'])
    btns.pack(fill='x', pady=(8, 4), padx=16)
    
    # Start Scraping button (main action) - rounded with effects
    btn_start = create_rounded_button(btns, 'Lancer le scraping', start_scraping, 'primary')
    btn_start.pack(fill='x', pady=(0, 8))
    
    # Row for Save / Save As (appears after scraping completes)
    save_row = tk.Frame(btns, bg=get_theme_colors()['bg'])
    # hidden by default; will be packed after completion

    # Quick relaunch row (under dropdowns)
    quick_row = tk.Frame(root, bg=get_theme_colors()['bg'])
    # Button to relaunch scraping quickly (skip cookies & navigation)
    def relaunch_quick():
        try:
            import config as _cfg
            _cfg.QUICK_RESCRAPE = True
        except Exception:
            pass
        # simulate a start with current selections
        start_scraping()
        try:
            import config as _cfg
            _cfg.QUICK_RESCRAPE = False
        except Exception:
            pass
    btn_quick = create_rounded_button(quick_row, 'Relancer le scraping', relaunch_quick, 'secondary')
    btn_quick.pack(fill='x')
    
    # Bottom buttons fixed at the very bottom of the window - never move
    bottom_btns = tk.Frame(root, bg=get_theme_colors()['bg'])
    bottom_btns.pack(side='bottom', fill='x', padx=16, pady=(0, 8))
    
    def open_logs():
        try:
            # Prefer project-level 'icicine_automation.log' if present, else fallback to config.LOG_FILE
            candidate1 = os.path.join(os.getcwd(), 'icicine_automation.log')
            log_path = candidate1 if os.path.exists(candidate1) else config.LOG_FILE
            # ensure directory and file exist
            os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)
            if not os.path.exists(log_path):
                with open(log_path, 'w', encoding='utf-8') as _f:
                    _f.write('')
            set_status('Ouverture du fichier de logs...')
            abs_path = os.path.abspath(log_path)
            if os.name == 'nt':
                os.startfile(abs_path)  # type: ignore[attr-defined]
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.Popen([opener, abs_path])
        except Exception:
            logging.exception('Failed to open log file.')
            set_status('Impossible d\'ouvrir le fichier de logs')

    btn_logs = create_rounded_button(bottom_btns, 'Logs', open_logs, 'secondary')
    btn_logs.pack(side='left', padx=(0, 8))
    
    def save_as_csv():
        try:
            rows = get_rows() if callable(get_rows) else []
            if not rows:
                logging.info('Nothing to save yet (no rows).')
                set_status('Rien à sauvegarder')
                return
            dest = fd.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')], title='Enregistrer sous')
            if not dest:
                return
            path = write_csv_to_path(rows, dest)
            if path:
                logging.info(f'💾 CSV saved: {path}')
                set_status('CSV sauvegardé')
                # Hide save buttons after saving
                try:
                    save_row.pack_forget()
                except Exception:
                    pass
        except Exception as e:
            logging.exception('Save failed: %s', e)
            set_status('Erreur de sauvegarde')

    def auto_save_csv():
        try:
            rows = get_rows() if callable(get_rows) else []
            if not rows:
                logging.info('Nothing to save yet (no rows).')
                set_status('Rien à sauvegarder')
                return
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            
            # Get cinema name and selected date for filename
            cinema_name = "Unknown"
            selected_date = datetime.today().strftime('%Y-%m-%d')
            try:
                if rows:
                    cinema_name = rows[0].get('cinema_name', 'Unknown')
                # Get selected date from GUI
                idx = date_combo.current()
                if idx < len(date_values):
                    selected_date = date_values[idx]
            except Exception:
                pass
            
            from csv_writer import generate_csv_filename
            filename = generate_csv_filename(cinema_name, selected_date)
            dest = os.path.join(config.OUTPUT_DIR, filename)
            path = write_csv_to_path(rows, dest)
            if path:
                logging.info(f'💾 CSV saved: {path}')
                set_status('CSV sauvegardé')
                # Hide save buttons after saving
                try:
                    save_row.pack_forget()
                except Exception:
                    pass
        except Exception as e:
            logging.exception('Auto-save failed: %s', e)
            set_status('Erreur de sauvegarde')

    # Save buttons created but not packed until completion
    btn_save_as = create_rounded_button(save_row, 'Save As', save_as_csv, 'secondary')
    btn_save = create_rounded_button(save_row, 'Save', auto_save_csv, 'secondary')
    btn_save.pack(side='left', padx=(0, 8))
    btn_save_as.pack(side='left')

    # Close button on far right in red; close GUI and quit driver only
    def close_gui_only():
        try:
            quit_driver()
        finally:
            root.destroy()
            logging.info('GUI closed by user.')

    btn_close = create_rounded_button(bottom_btns, 'Fermer', close_gui_only, 'danger')
    btn_close.pack(side='right')

    # Default geometry
    root.geometry('480x450')

    def check_inactivity():
        # Only enforce auto-close if a positive inactivity timeout is provided
        if inactivity is not None and inactivity > 0:
            if time.time() - last_action > inactivity:
                logging.info('Auto-closing due to inactivity.')
                close_all()
                return
        root.after(100, check_inactivity)

    # Treat user interactions as activity to reset the timer
    def _mark_active(event=None):
        nonlocal last_action
        last_action = time.time()
    for seq in ('<Any-KeyPress>', '<Any-Button>', '<Motion>'):
        root.bind_all(seq, _mark_active, add='+')

    # Responsive logo sizing
    def _load_original_logo():
        nonlocal original_logo_img
        try:
            if os.path.exists(logo_path):
                original_logo_img = Image.open(logo_path).convert('RGBA')
        except Exception:
            logging.exception('Failed to load logo image.')

    def _resize_logo(event=None):
        nonlocal logo_photo, original_logo_img
        if original_logo_img is None:
            return
        # Keep logo small and proportional to window size
        w = root.winfo_width() or 480
        h = root.winfo_height() or 450
        target = int(min(w, h) * 0.12)  # small logo ~12% of min dimension
        target = max(48, min(128, target))
        try:
            img = original_logo_img.copy()
            img.thumbnail((target, target), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(img)
            logo_label.configure(image=logo_photo)
            logo_label.image = logo_photo
        except Exception:
            logging.exception('Failed to resize logo image.')

    _load_original_logo()
    _resize_logo()
    root.bind('<Configure>', _resize_logo)

    root.after(100, check_inactivity)
    root.mainloop()