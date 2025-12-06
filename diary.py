import json
import os 
import sys
import datetime
import textwrap

DATA_FILE = "addit87_diary.json"

class C: 
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"entries": [], "next_id": 1}
    try: 
        with open(DATA_FILE, "r", encoding = "utf-8") as f:
            return json.load(f)
    except Exception:
        print(f"{C.RED}Corrupted data file. Creating a fresh one.{C.RESET}")
        return {"entries": [], "next_id": 1}
    
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def banner():
    title = f"{C.GREEN}{C.BOLD}Addit '87{C.RESET}"
    tabs = (
        f"{C.CYAN}WEEKLY DIARY{C.RESET}"
        f"{C.DIM}EXPENSES ADDRESSES SHOPPING TO-DO{C.RESET}"
    )
    print (title)
    print (tabs)
    print ("-" * 60)

def date_today_str():
    return datetime.date.today().isoformat()

def iso_week(dt):
    return dt.isocalendar().week

def weekday_name(dt):
    return dt.strftime("%A")

def add_entry(data):
    print(f"{C.RED}ADD ENTRY{C.RESET} - End input with a single '.' on a new line.")
    date_str = input(f"{C.CYAN}Date (YYYY-MM-DD) [{date_today_str}]: {C.RESET}").strip()
    if not date_str:
        date_str = date_today_str()
    
    try:
        dt = datetime.date.fromisoformat(date_str)
    except ValueError:
        print(f"{C.RED}Invalid date. Use YYYY-MM-DD.{C.RESET}")
        return
    
    title = input(f"{C.CYAN}Title (optional): {C.RESET}").strip()

    print(f"{C.CYAN}Entry (multi-line):{C.RESET}")
    lines = []
    while True:
        line = input ()
        if line.strip() == ".":
            break
        lines.append(line)
    content = "\n".join(lines).strip()

    if not content:
        print(f"{C.RED}Empty entry discarded.{C.RESET}")
        return
    
    entry_id = data["next_id"]
    data["next_id"] += 1

    entry = {
        "id": entry_id,
        "date": date_str,
        "weekday": weekday_name(dt),
        "iso_week": iso_week(dt),
        "title": title,
        "content": content,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    data["entries"].append(entry)
    save_data(data)
    print(f"{C.GREEN}Saved entry #{entry_id} ({date_str}, Week {entry['iso_week']}).{C.RESET}")

def list_entries(data, limit=20):
    entries = sorted(data["entries"], key=lambda e: (e["date"], e["id"]))
    if not entries:
        print(f"{C.DIM}No entries yet. Use 'add' to start.{C.RESET}")
        return
    print(f"{C.RED}WEEKLY DIARY - latest {limit}{C.RESET}")
    for e in entries[-limit:]:
        title = f" - {e['title']}" if e["title"] else ""
        print(
            f"{C.GREEN}#{e['id']}{C.RESET} {e['date']} ({e['weekday']}, W{e['iso_week']}){title}"   
        )

def list_weeks(data):
    weeks = sorted({e["iso_week"] for e in data["entries"]})
    if not weeks:
        print(f"{C.DIM}No weeks yet. Add an entry first.{C.RESET}")
        return
    print(f"{C.RED}WEEKS INDEX{C.RESET}")
    print(", ".join(f"W{w}" for w in weeks))

def entries_by_week(data, week_num):
    try:
        w = int (week_num)
    except ValueError:
        print(f"{C.RED}Week must be a number(1-53).{C.RESET}")
        return
    filtered = [e for e in data["entries"] if e["iso_week"] == w]
    if not filtered:
        print(f"{C.DIM}No entries for Week{w}. {C.RESET}")
        return
    print (f"{C.RED}WEEK {w}{C.RESET}")
    for e in sorted(filtered, key=lambda e: (e["date"], e["id"])):
        title = f" - {e['title']}" if e ["title"] else ""
        print (f"{C.GREEN}#{e['id']}{C.RESET} {e['date']} ({e['weekday']}){title}")

## !!! 
## DELETE AND EDIT STILL LACKING 
## !!!
