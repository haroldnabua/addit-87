def get_terminal_width():
    """Get terminal width for centering"""
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except:
        return 80#!/usr/bin/env python3
"""
Addit '87 - Retro CLI Journal (Full Navigation)

Drop into addit87.py and run:
    python addit87.py

Or build as executable:
    pip install pyinstaller
    pyinstaller --onefile --name "Addit87" --icon=icon.ico addit87.py
"""

import json
import os
import sys
import datetime
import textwrap
import time
import tempfile
import subprocess

# For keyboard input
if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix/Linux/Mac
    import tty
    import termios

TEXT_WRAP_WIDTH = 70
LEFT_MARGIN = 5  # Base margin for everything
SIDEBAR_WIDTH = 15  # Width for the sidebar column
CONTENT_SPACING = 3  # Space between sidebar and content
CATEGORIES = ["WEEKLY DIARY", "EXPENSES", "ADDRESSES", "SHOPPING", "TO DO"]
CATEGORY_FILES = {
    "WEEKLY DIARY": "addit87_diary.json",
    "EXPENSES": "addit87_expenses.json",
    "ADDRESSES": "addit87_addresses.json",
    "SHOPPING": "addit87_shopping.json",
    "TO DO": "addit87_todo.json"
}

class AppState:
    def __init__(self):
        self.category_index = 0
        self.entry_index = 0
        self.mode = "browse"  # browse, add, edit, view
        
    @property
    def current_category(self):
        return CATEGORIES[self.category_index]
    
    @property
    def data_file(self):
        return CATEGORY_FILES[self.current_category]

state = AppState()

class C:
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    WHITE = "\033[97m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    BG_RED = "\033[41m"
    BG_BLACK = "\033[40m"
    RESET = "\033[0m"

def enable_ansi_on_windows():
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            try:
                os.system("")
            except Exception:
                pass

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_data():
    if not os.path.exists(state.data_file):
        return {"entries": [], "next_id": 1}
    try:
        with open(state.data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"entries": [], "next_id": 1}

def save_data(data):
    with open(state.data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def date_today_str():
    return datetime.date.today().isoformat()

def iso_year_week(dt):
    iso = dt.isocalendar()
    return int(iso[0]), int(iso[1])

def weekday_name(dt):
    return dt.strftime("%A")

def get_key():
    """Get a single keypress - blocking version"""
    if os.name == 'nt':  # Windows
        key = msvcrt.getch()
        if key == b'\xe0' or key == b'\x00':
            key = msvcrt.getch()
            if key == b'K': return 'LEFT'
            elif key == b'M': return 'RIGHT'
            elif key == b'H': return 'UP'
            elif key == b'P': return 'DOWN'
        elif key == b'\r': return 'ENTER'
        elif key == b'\x1b': return 'ESC'
        elif key == b'a' or key == b'A': return 'a'
        elif key == b'd' or key == b'D': return 'd'
        elif key == b'e' or key == b'E': return 'e'
        elif key == b'q' or key == b'Q': return 'q'
        return None
    else:  # Unix/Linux/Mac
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'D': return 'LEFT'
                    elif ch3 == 'C': return 'RIGHT'
                    elif ch3 == 'A': return 'UP'
                    elif ch3 == 'B': return 'DOWN'
                return 'ESC'
            elif ch == '\r' or ch == '\n': return 'ENTER'
            elif ch.lower() == 'a': return 'a'
            elif ch.lower() == 'd': return 'd'
            elif ch.lower() == 'e': return 'e'
            elif ch.lower() == 'q': return 'q'
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

def draw_header():
    """Draw the header with category navigation"""
    ascii_art = f"""{C.GREEN}{C.BOLD}
   ╔═══════════════════════════════╗
   ║                               ║
   ║      A D D I T   ' 8 7        ║
   ║                               ║
   ╚═══════════════════════════════╝
{C.RESET}"""
    print(ascii_art)
    
    # Menu categories
    menu_parts = []
    for i, cat in enumerate(CATEGORIES):
        if i == state.category_index:
            menu_parts.append(f"{C.WHITE}{C.BOLD} {cat} {C.RESET}")
        else:
            menu_parts.append(f"{C.BG_RED}{C.WHITE} {cat} {C.RESET}")
    
    print(" ".join(menu_parts))
    print()

def draw_sidebar(data):
    """Draw the sidebar with entries"""
    entries = sorted(data.get("entries", []), key=lambda e: (e["date"], e["id"]))
    
    if not entries:
        return []
    
    sidebar_lines = []
    
    # For WEEKLY DIARY, group by week. For others, just list by title
    if state.current_category == "WEEKLY DIARY":
        # Group by week
        weeks = {}
        for e in entries:
            week = int(e.get("iso_week", 0))
            if week not in weeks:
                weeks[week] = []
            weeks[week].append(e)
        
        for week_num in sorted(weeks.keys(), reverse=True):
            week_entries = weeks[week_num]
            for e in week_entries:
                sidebar_lines.append({
                    "week": week_num,
                    "id": e["id"],
                    "date": e.get("formatted_date", e["date"]),
                    "title": e.get("title", "")[:20],
                    "entry": e,
                    "display": f"WEEK {week_num:2d}"
                })
    else:
        # For other categories, show title
        for e in reversed(entries):
            title = e.get("title", "Untitled")[:30]
            sidebar_lines.append({
                "week": None,
                "id": e["id"],
                "date": e.get("formatted_date", e["date"]),
                "title": title,
                "entry": e,
                "display": title
            })
    
    return sidebar_lines

def draw_screen(data, sidebar_lines, selected_entry_data=None):
    """Draw the complete screen - everything horizontally aligned"""
    clear_screen()
    draw_header()
    
    margin = " " * LEFT_MARGIN
    
    if not sidebar_lines:
        print(f"{margin}{C.DIM}No entries. Press 'A' to add.{C.RESET}")
        return
    
    # Prepare sidebar items (limit to 10)
    sidebar_items = []
    for i, item in enumerate(sidebar_lines[:10]):
        display = item['display'][:SIDEBAR_WIDTH-2]
        if i == state.entry_index:
            sidebar_items.append(f"{C.BG_RED}{C.WHITE}{C.BOLD} {display:<{SIDEBAR_WIDTH-2}} {C.RESET}")
        else:
            sidebar_items.append(f"{C.WHITE} {display:<{SIDEBAR_WIDTH-2}}{C.RESET}")
    
    # Prepare content lines
    content_lines = []
    if selected_entry_data:
        e = selected_entry_data
        
        # Only show date for WEEKLY DIARY
        if state.current_category == "WEEKLY DIARY":
            date_text = e.get('formatted_date', e['date'])
            content_lines.append(f"{C.CYAN}{date_text}{C.RESET}")
            content_lines.append("")
            
            # Show title for Weekly Diary
            if e.get("title"):
                content_lines.append(f"{C.CYAN}{e['title']}{C.RESET}")
                content_lines.append("")
        
        # For other categories, don't show title (it's in the sidebar already)
        
        content = e.get("content", "")
        lines = content.split('\n')
        for line in lines:
            content_lines.append(f"{C.CYAN}{line}{C.RESET}")
    
    # Draw side-by-side - all aligned with same left margin
    max_rows = max(len(sidebar_items), len(content_lines))
    spacing = " " * CONTENT_SPACING
    
    for i in range(max_rows):
        # Start with base margin
        line = margin
        
        # Add sidebar item
        if i < len(sidebar_items):
            line += sidebar_items[i]
        else:
            line += " " * SIDEBAR_WIDTH
        
        # Add spacing
        line += spacing
        
        # Add content
        if i < len(content_lines):
            line += content_lines[i]
        
        print(line)
    
    print()
    
    # Controls - aligned with same margin
    controls = "← → = Category | ↑ ↓ = Entry | A = Add | E = Edit | D = Delete | Q = Quit"
    print(f"{margin}{C.DIM}{controls}{C.RESET}")

def add_entry_interactive():
    """Add a new entry"""
    data = load_data()
    
    clear_screen()
    draw_header()
    print(f"{C.CYAN}ADD NEW ENTRY{C.RESET}\n")
    
    # Only ask for date in WEEKLY DIARY
    if state.current_category == "WEEKLY DIARY":
        default_date = date_today_str()
        date_str = input(f"Date (YYYY-MM-DD) [{default_date}]: ").strip() or default_date
        
        try:
            dt = datetime.date.fromisoformat(date_str)
        except ValueError:
            print(f"{C.RED}Invalid date.{C.RESET}")
            time.sleep(1)
            return
        
        formatted_date = dt.strftime("%A, %B %d, %Y.")
        iso_y, iso_w = iso_year_week(dt)
    else:
        # For other categories, use current date but don't show it
        dt = datetime.date.today()
        date_str = dt.isoformat()
        formatted_date = ""
        iso_y, iso_w = iso_year_week(dt)
    
    # Get title
    title = input(f"Title: ").strip()
    
    # Get content
    print(f"\nContent (end with '.'):\n")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == ".":
                break
            lines.append(line)
        except (EOFError, KeyboardInterrupt):
            return
    
    content = "\n".join(lines).strip()
    if not content:
        return
    
    # Save
    entry_id = data.get("next_id", 1)
    data["next_id"] = entry_id + 1
    
    entry = {
        "id": entry_id,
        "date": date_str,
        "formatted_date": formatted_date,
        "weekday": weekday_name(dt),
        "iso_year": iso_y,
        "iso_week": iso_w,
        "title": title,
        "content": content,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    
    data.setdefault("entries", []).append(entry)
    save_data(data)

def delete_entry_interactive(entry_id):
    """Delete an entry"""
    data = load_data()
    data["entries"] = [e for e in data.get("entries", []) if e.get("id") != entry_id]
    save_data(data)
    state.entry_index = max(0, state.entry_index - 1)

def edit_entry_interactive(entry):
    """Edit an entry using external text editor"""
    data = load_data()
    
    clear_screen()
    draw_header()
    print(f"{C.CYAN}EDIT ENTRY #{entry['id']}{C.RESET}\n")
    
    # Edit title
    current_title = entry.get("title", "")
    print(f"Current title: {C.YELLOW}{current_title}{C.RESET}")
    new_title = input(f"New title (press Enter to keep current): ").strip()
    if new_title:
        entry["title"] = new_title
    
    # Edit content using external editor
    print(f"\nOpening text editor to edit content...")
    print(f"{C.DIM}Make your changes, then save and close the editor.{C.RESET}\n")
    
    input("Press Enter to open editor...")
    
    # Create temporary file with current content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
        tf.write(entry.get('content', ''))
        temp_path = tf.name
    
    try:
        # Open editor based on OS
        if os.name == 'nt':  # Windows
            os.system(f'notepad "{temp_path}"')
        else:  # Linux/Mac
            editor = os.environ.get('EDITOR', 'nano')
            os.system(f'{editor} "{temp_path}"')
        
        # Read back the edited content
        with open(temp_path, 'r', encoding='utf-8') as tf:
            new_content = tf.read().strip()
        
        if new_content:
            entry["content"] = new_content
    
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass
    
    entry["modified_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    
    # Save back
    for i, e in enumerate(data["entries"]):
        if e["id"] == entry["id"]:
            data["entries"][i] = entry
            break
    
    save_data(data)

def main():
    enable_ansi_on_windows()
    
    # Initial draw
    data = load_data()
    sidebar_lines = draw_sidebar(data)
    selected_entry = None
    if sidebar_lines and state.entry_index < len(sidebar_lines):
        selected_entry = sidebar_lines[state.entry_index]["entry"]
    draw_screen(data, sidebar_lines, selected_entry)
    
    while True:
        # Wait for input (blocking - no continuous refresh)
        key = get_key()
        
        if not key:
            continue
        
        if key == 'LEFT':
            state.category_index = (state.category_index - 1) % len(CATEGORIES)
            state.entry_index = 0
        elif key == 'RIGHT':
            state.category_index = (state.category_index + 1) % len(CATEGORIES)
            state.entry_index = 0
        elif key == 'UP':
            data = load_data()
            sidebar_lines = draw_sidebar(data)
            if sidebar_lines:
                state.entry_index = (state.entry_index - 1) % len(sidebar_lines)
        elif key == 'DOWN':
            data = load_data()
            sidebar_lines = draw_sidebar(data)
            if sidebar_lines:
                state.entry_index = (state.entry_index + 1) % len(sidebar_lines)
        elif key == 'a':
            add_entry_interactive()
        elif key == 'e':
            data = load_data()
            sidebar_lines = draw_sidebar(data)
            if sidebar_lines and state.entry_index < len(sidebar_lines):
                selected_entry = sidebar_lines[state.entry_index]["entry"]
                edit_entry_interactive(selected_entry)
        elif key == 'd':
            data = load_data()
            sidebar_lines = draw_sidebar(data)
            if sidebar_lines and state.entry_index < len(sidebar_lines):
                selected_entry = sidebar_lines[state.entry_index]["entry"]
                delete_entry_interactive(selected_entry["id"])
        elif key == 'q':
            clear_screen()
            print(f"\n{C.CYAN}Goodbye!{C.RESET}\n")
            break
        else:
            continue
        
        # Redraw after action
        data = load_data()
        sidebar_lines = draw_sidebar(data)
        selected_entry = None
        if sidebar_lines and state.entry_index < len(sidebar_lines):
            selected_entry = sidebar_lines[state.entry_index]["entry"]
        draw_screen(data, sidebar_lines, selected_entry)

if __name__ == "__main__":
    main()