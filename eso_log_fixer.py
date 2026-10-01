"""
=============================================================================
ESO Encounter Log Fixer (Class + Race + CP Fingerprint)
Author:  @SixteenthMatt
Version: 1.0.0
Updated: 9/30/2026
Description: Automatically parses and patches ESO encounter logs to restore 
             missing player character names and @gamertags using class, 
             race, and Champion Point fingerprints.

DISCLAIMER OF LIABILITY:
This software is for entertainment purposes only and provided "as is", 
without warranty of any kind, express or implied, including but not 
limited to fitness for a particular purpose. In no event shall the 
author be held liable for any damages, log corruption, account issues, 
or other liability arising from the use of this software.
USE AT YOUR OWN RISK.
=============================================================================
"""

__author__ = "@YourGamertag"
__version__ = "1.0.0"

import csv
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ESO Class Mappings
CLASS_NAMES = {
    1: "Dragonknight",
    2: "Sorcerer",
    3: "Nightblade",
    4: "Warden",
    5: "Necromancer",
    6: "Templar",
    117: "Arcanist",
}

CLASS_ALIASES = {
    "1": 1, "dk": 1, "dragonknight": 1,
    "2": 2, "sorc": 2, "sorcerer": 2,
    "3": 3, "nb": 3, "nightblade": 3,
    "4": 4, "warden": 4, "ward": 4,
    "5": 5, "necro": 5, "necromancer": 5,
    "6": 6, "templar": 6, "plar": 6,
    "117": 117, "arc": 117, "arcanist": 117,
}


class ESOLogFixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"ESO Encounter Log Fixer — by {__author__}")
        self.root.geometry("820x760")
        self.root.minsize(680, 520)

        self.log_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.cp_buffer = tk.IntVar(value=5)

        self._build_ui()

    def _build_ui(self):
        pad = {'padx': 10, 'pady': 5}

        # 1. File Selection Frame
        file_frame = ttk.LabelFrame(self.root, text="Log Files")
        file_frame.pack(fill=tk.X, **pad)

        ttk.Label(file_frame, text="Input Log:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(file_frame, textvariable=self.log_file_path, width=55).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse...", command=self._browse_log).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(file_frame, text="Output Log:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(file_frame, textvariable=self.output_file_path, width=55).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(file_frame, text="Change...", command=self._browse_output).grid(row=1, column=2, padx=5, pady=2)
        file_frame.columnconfigure(1, weight=1)

        # 2. Roster Input Frame
        roster_frame = ttk.LabelFrame(self.root, text="Roster Definition (@Gamertag with spaces, Class, Starting CP)")
        roster_frame.pack(fill=tk.BOTH, expand=True, **pad)

        ctrl_bar = ttk.Frame(roster_frame)
        ctrl_bar.pack(fill=tk.X, padx=5, pady=3)
        ttk.Button(ctrl_bar, text="Auto-Detect Full Roster", command=self._detect_roster_from_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_bar, text="Copy Roster to Clipboard", command=self._copy_roster_to_clipboard).pack(side=tk.LEFT, padx=6)
        ttk.Button(ctrl_bar, text="Clear", command=lambda: self.roster_text.delete("1.0", tk.END)).pack(side=tk.RIGHT, padx=2)

        self.roster_text = tk.Text(roster_frame, height=14, font=("Consolas", 10))
        self.roster_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)

        sample_roster = (
            "@Main Tank 5 2990\n"
            "@Off Tank Necromancer 2087\n"
            "@Healer One Nightblade 2049\n"
            "@Healer Two Warden 2484\n"
            "@DPS DK 1 2479\n"
            "@Templar DPS 6 2209\n"
            "@Arcanist Lead 117 2900\n"
            "@Arcanist Alt Arcanist 990\n"
            "@Stam Blade 3 2999\n"
            "@Arcanist DPS 117 2543\n"
            "@Mag Blade 3 2312\n"
            "@Sorc DPS Sorcerer 2390\n"
            "@Late Sub Arcanist 2540  # [Joined +01:14:22]"
        )
        self.roster_text.insert(tk.END, sample_roster)

        # 3. Tuning & Execution Frame
        exec_frame = ttk.Frame(self.root)
        exec_frame.pack(fill=tk.X, **pad)

        ttk.Label(exec_frame, text="Max Level-Up CP Buffer:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(exec_frame, from_=1, to=20, textvariable=self.cp_buffer, width=5).pack(side=tk.LEFT, padx=5)

        self.start_btn = ttk.Button(exec_frame, text="Fix & Patch Log", command=self._start_processing)
        self.start_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10, ipady=3)

        # 4. Status / Console
        status_frame = ttk.LabelFrame(self.root, text="Processing Console")
        status_frame.pack(fill=tk.BOTH, expand=True, **pad)

        self.console = tk.Text(status_frame, height=8, state=tk.DISABLED, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 5. Disclaimer Footer
        disclaimer_lbl = ttk.Label(
            self.root,
            text="Provided 'as-is' for personal use. Use at your own risk — the author accepts no liability.",
            font=("Segoe UI", 8),
            foreground="#777777"
        )
        disclaimer_lbl.pack(side=tk.BOTTOM, pady=(0, 5))

    def _copy_roster_to_clipboard(self):
        text = self.roster_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Notice", "Roster box is currently empty.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Copied", "Roster copied to clipboard!")

    def _log(self, message):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def _browse_log(self):
        path = filedialog.askopenfilename(
            filetypes=[("ESO Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.log_file_path.set(path)
            base, ext = os.path.splitext(path)
            self.output_file_path.set(f"{base}_fixed{ext}")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("ESO Log Files", "*.log"), ("Text Files", "*.txt")]
        )
        if path:
            self.output_file_path.set(path)

    def _detect_roster_from_log(self):
        in_path = self.log_file_path.get()
        if not os.path.isfile(in_path):
            messagebox.showwarning("Notice", "Select an input log file first.")
            return

        max_buf = self.cp_buffer.get()
        detected = []
        start_ts = None

        try:
            with open(in_path, 'r', encoding='utf-8', errors='replace') as infile:
                for line in infile:
                    if start_ts is None:
                        first_val = line.split(',', 1)[0]
                        if first_val.isdigit():
                            start_ts = int(first_val)

                    if "UNIT_ADDED" not in line or ",PLAYER," not in line:
                        continue

                    row = next(csv.reader([line.rstrip('\r\n')]))
                    if len(row) < 18 or row[1] != "UNIT_ADDED" or row[3] != "PLAYER":
                        continue

                    try:
                        ts = int(row[0])
                        class_id = int(row[8])
                        race_id = int(row[9])
                        cp = int(row[14])
                    except ValueError:
                        continue

                    if start_ts is None:
                        start_ts = ts

                    matched = None
                    for p in detected:
                        if p['class_id'] == class_id and p['race_id'] == race_id:
                            if abs(cp - p['cp']) <= max_buf:
                                matched = p
                                break

                    if matched:
                        if cp > matched['cp']:
                            matched['cp'] = cp
                        continue

                    if row[16] != "PLAYER_ALLY" or row[17] != "T":
                        continue

                    rel_sec = max(0, (ts - start_ts) // 1000)
                    hours = rel_sec // 3600
                    mins = (rel_sec % 3600) // 60
                    secs = rel_sec % 60
                    time_str = f"+{hours:02d}:{mins:02d}:{secs:02d}"

                    is_late = (len(detected) >= 12) or (rel_sec > 180)
                    is_self = (row[4] == 'T')
                    class_str = CLASS_NAMES.get(class_id, str(class_id))
                    existing_char = row[10].strip() if len(row) > 10 else ""
                    existing_account = row[11].strip() if len(row) > 11 else ""

                    if existing_account:
                        tag = existing_account if existing_account.startswith('@') else f"@{existing_account}"
                    elif existing_char:
                        tag = f"@{existing_char}"
                    elif is_self:
                        tag = "@Your Gamer Tag"
                    else:
                        tag = f"@Gamer Tag {len(detected) + 1}"

                    detected.append({
                        'tag': tag,
                        'class_id': class_id,
                        'class_str': class_str,
                        'race_id': race_id,
                        'cp': cp,
                        'is_late': is_late,
                        'time_str': time_str
                    })

            if detected:
                self.roster_text.delete("1.0", tk.END)
                out_lines = []
                for p in detected:
                    base = f"{p['tag']} {p['class_str']} {p['cp']}"
                    if p['is_late']:
                        out_lines.append(f"{base}  # [Joined {p['time_str']}]")
                    else:
                        out_lines.append(base)

                self.roster_text.insert(tk.END, "\n".join(out_lines))

                initial_cnt = sum(1 for p in detected if not p['is_late'])
                late_cnt = sum(1 for p in detected if p['is_late'])
                self._log(f"Detected {len(detected)} total players ({initial_cnt} initial, {late_cnt} late joiners).")
                for p in detected:
                    if p['is_late']:
                        self._log(f"  Late joiner: {p['tag']} ({p['class_str']}, Race {p['race_id']}, CP {p['cp']}) at {p['time_str']}")
            else:
                messagebox.showwarning("Scan", "No valid PLAYER UNIT_ADDED entries found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed reading log: {e}")

    def _parse_roster(self):
        raw_lines = self.roster_text.get("1.0", tk.END).strip().splitlines()
        players = []

        for line in raw_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            line = line.split('#')[0].strip()
            if not line:
                continue

            cp_match = re.search(r'\s+(\d+)\s*$', line)
            if not cp_match:
                continue

            cp = int(cp_match.group(1))
            prefix = line[:cp_match.start()].strip().rstrip(',').strip()
            if not prefix:
                continue

            tokens = prefix.split()
            last_word = tokens[-1].lower().strip("()")

            class_id = None
            if last_word in CLASS_ALIASES:
                class_id = CLASS_ALIASES[last_word]
                name_part = " ".join(tokens[:-1]).strip().rstrip(',').strip()
            else:
                name_part = prefix

            if not name_part:
                continue

            if name_part.startswith('@'):
                gamertag = name_part
                char_name = name_part[1:].strip()
            else:
                gamertag = f"@{name_part}"
                char_name = name_part

            players.append({
                'char_name': char_name,
                'gamertag': gamertag,
                'class_id': class_id,
                'race_id': None,
                'initial_cp': cp,
                'current_cp': cp
            })

        return players

    def _start_processing(self):
        in_path = self.log_file_path.get()
        out_path = self.output_file_path.get()

        if not os.path.isfile(in_path):
            messagebox.showerror("Error", "Please select a valid input log file.")
            return

        players = self._parse_roster()
        if not players:
            messagebox.showerror("Error", "No valid roster entries could be parsed.")
            return

        self.start_btn.config(state=tk.DISABLED)
        t = threading.Thread(target=self._process_log_thread, args=(in_path, out_path, players))
        t.daemon = True
        t.start()

    def _process_log_thread(self, in_path, out_path, players):
        try:
            max_buf = self.cp_buffer.get()
            self._log(f"Processing: {os.path.basename(in_path)}")
            self._log(f"Roster size: {len(players)} players (Max CP level-up buffer: +{max_buf})")

            active_units = {}
            replaced_added = 0
            replaced_changed = 0
            reassigned_count = 0
            cp_level_ups = 0

            def get_or_rebind_player(unit_id, class_id, race_id, current_log_cp):
                nonlocal reassigned_count, cp_level_ups

                if unit_id in active_units:
                    p = active_units[unit_id]
                    class_ok = (p['class_id'] is None or p['class_id'] == class_id)
                    race_ok = (p['race_id'] is None or p['race_id'] == race_id)
                    cp_diff = current_log_cp - p['current_cp']
                    cp_ok = (0 <= cp_diff <= max_buf) or (p['initial_cp'] == current_log_cp)

                    if class_ok and race_ok and cp_ok:
                        if p['race_id'] is None:
                            p['race_id'] = race_id
                            self._log(f"Locked Fingerprint: {p['gamertag']} -> Class {class_id}, Race {race_id}")

                        if current_log_cp > p['current_cp']:
                            cp_level_ups += 1
                            self._log(f"Level-up: {p['gamertag']} (Unit {unit_id}) {p['current_cp']} -> {current_log_cp}")
                            p['current_cp'] = current_log_cp
                        return p
                    else:
                        reassigned_count += 1
                        del active_units[unit_id]

                best_match = None
                best_score = 9999

                for p in players:
                    if p['class_id'] is not None and p['class_id'] != class_id:
                        continue
                    if p['race_id'] is not None and p['race_id'] != race_id:
                        continue

                    diff = current_log_cp - p['current_cp']
                    if -1 <= diff <= max_buf:
                        score = abs(diff)
                        if p['race_id'] == race_id:
                            score -= 0.1
                        if score < best_score:
                            best_score = score
                            best_match = p

                if best_match:
                    if best_match['race_id'] is None:
                        best_match['race_id'] = race_id
                        self._log(f"Locked Fingerprint: {best_match['gamertag']} -> Class {class_id}, Race {race_id}")

                    if current_log_cp > best_match['current_cp']:
                        cp_level_ups += 1
                        self._log(f"Level-up: {best_match['gamertag']} {best_match['current_cp']} -> {current_log_cp}")
                        best_match['current_cp'] = current_log_cp

                    active_units[unit_id] = best_match
                    return best_match

                return None

            with open(in_path, 'r', encoding='utf-8', errors='replace') as infile, \
                 open(out_path, 'w', encoding='utf-8', errors='replace') as outfile:

                for line in infile:
                    if "UNIT_ADDED" not in line and "UNIT_CHANGED" not in line:
                        outfile.write(line)
                        continue

                    row = next(csv.reader([line.rstrip('\r\n')]))
                    event_type = row[1] if len(row) > 1 else ""

                    if event_type == "UNIT_ADDED" and len(row) >= 15 and row[3] == "PLAYER":
                        unit_id = row[2]
                        try:
                            class_id = int(row[8])
                            race_id = int(row[9])
                            cp = int(row[14])
                        except ValueError:
                            outfile.write(line)
                            continue

                        matched = get_or_rebind_player(unit_id, class_id, race_id, cp)
                        if matched:
                            row[10] = matched['char_name']
                            row[11] = matched['gamertag']
                            replaced_added += 1

                            out_row = [f'"{val}"' if i in (10, 11) else val for i, val in enumerate(row)]
                            outfile.write(",".join(out_row) + "\n")
                            continue

                    elif event_type == "UNIT_CHANGED" and len(row) >= 10:
                        unit_id = row[2]
                        try:
                            class_id = int(row[3])
                            race_id = int(row[4])
                            cp = int(row[9])
                        except ValueError:
                            outfile.write(line)
                            continue

                        matched = get_or_rebind_player(unit_id, class_id, race_id, cp)
                        if matched:
                            row[5] = matched['char_name']
                            row[6] = matched['gamertag']
                            replaced_changed += 1

                            out_row = [f'"{val}"' if i in (5, 6) else val for i, val in enumerate(row)]
                            outfile.write(",".join(out_row) + "\n")
                            continue

                    outfile.write(line)

            self._log("-----------------------------------------")
            self._log(f"Complete! Saved to: {os.path.basename(out_path)}")
            self._log(f"Patched UNIT_ADDED:          {replaced_added}")
            self._log(f"Patched UNIT_CHANGED:        {replaced_changed}")
            self._log(f"Unit ID Collisions Resolved: {reassigned_count}")
            self._log(f"CP Level-Ups Tracked:        {cp_level_ups}")

            messagebox.showinfo(
                "Complete",
                f"Patch successful!\n\n"
                f"UNIT_ADDED lines fixed: {replaced_added}\n"
                f"UNIT_CHANGED lines fixed: {replaced_changed}\n"
                f"Unit ID collisions resolved: {reassigned_count}\n"
                f"Level-ups tracked: {cp_level_ups}"
            )
        except Exception as e:
            self._log(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.start_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = ESOLogFixerApp(root)
    root.mainloop()