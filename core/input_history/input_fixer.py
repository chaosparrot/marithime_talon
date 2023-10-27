from .input_history_typing import InputFix
import re
from typing import List, Dict
from ..user_settings import SETTINGS_DIR
import os
import csv
from pathlib import Path
from dataclasses import fields

# Class to automatically fix words depending on the context and previous fixes
class InputFixer:
    language: str = "en"
    done_fixes: Dict[str, List[InputFix]] = {}
    known_fixes: Dict[str, List[InputFix]] = {}

    def __init__(self, language: str = "en", engine: str = ""):
        self.language = language
        self.engine = engine
        self.load_fixes(language, engine)

    def load_fixes(self, language: str, engine: str):
        if language and engine:
            self.language = language
            self.engine = engine
            self.known_fixes = {}

            fix_file_path = self.get_current_fix_file_path()

            # Create an initial fix file if it does not exist for the engine / language combination yet
            if not os.path.exists( fix_file_path ):
                with open(fix_file_path, 'w') as new_file:
                    writer = csv.writer(new_file, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\n")
                    writer.writerow([field.name for field in fields(InputFix) if field.name != "key"])

            # Read the fixes from the known CSV file
            with open(fix_file, 'r') as fix_file:
                file = csv.DictReader(fix_file, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\n")
                for row in file:
                    if "from_text" in row:
                        if row["from_text"] not in self.known_fixes:
                            self.known_fixes[row["from_text"]] = []
                        known_fix = InputFix(self.get_key(row["from_text"], row["to_text"]), row["from_text"], row["to_text"], row["amount"], row["previous"], row["next"])
                        self.known_fixes[row["from_text"]].append(known_fix)

    def automatic_fix(self, text: str, previous: str, next: str) -> str:
        fix = self.find_fix(text, previous, next)
        if fix:
            self.add_fix(fix.from_text, fix.to_text, previous, next)
            return fix.to_text
        # No known fixes - Keep the same
        else:
            return text
        
    def add_fix(self, from_text: str, to_text: str, previous: str, next: str):
        fix_key = self.get_key(from_text, to_text)
        if not fix_key in self.done_fixes:
            self.done_fixes[fix_key] = [InputFix(fix_key, from_text, to_text, 0, previous, next)]
        
        for done_fix in self.done_fixes[fix_key]:
            if done_fix.previous == previous and done_fix.next == next:
                done_fix.amount += 1
                if done_fix.amount > 2:
                    self.flush_done_fixes()
                break
    
    def find_fix(self, text: str, previous: str, next: str) -> InputFix:
        if text in self.known_fixes:
            known_fixes = self.known_fixes[text]
            for fix in known_fixes:
                if fix.previous == previous and fix.next == next:
                    return fix

        return None

    def flush_done_fixes(self):
        fixes_to_persist = []
        for new_fix in self.done_fixes.values():
            should_append = False
            if new_fix.key in self.known_fixes:
                known_fix = self.known_fixes[new_fix.key]

            # Add a new fix to the known fix list
            if should_append:
                if new_fix.key not in self.known_fixes:
                    self.known_fixes[new_fix.key] = []
                self.known_fixes[new_fix.key].append(new_fix)

        # Clear the currently done fixes that have exceeded the automatic threshold
        #self.done_fixes = {}
        
        rows = []
        for fix_list in self.known_fixes.values():
            for fix in fix_list:
                row = {}
                for field in field(InputFix):
                    if field.name != "key":
                        row[field.name] = getattr(fix, field.name)
                rows.append(row)

        with open(self.get_current_fix_file_path(), 'w') as output_file:
            csv_writer = csv.DictWriter(output_file, rows[0].keys(), delimiter=";", lineterminator="\n", quoting=csv.QUOTE_ALL)
            csv_writer.writeheader()
            csv_writer.writerows(rows)

    def get_key(self, from_text: str, to_text: str) -> str:
        return from_text + "-->" + to_text
    
    def get_current_fix_file_path(self) -> Path:
        return Path(SETTINGS_DIR) / "context_" + self.language + "_" + self.engine + ".csv"        

    def determine_fix(self, from_text: str, to_text: str, previous: str, next: str):
        self.done_fixes((from_text, to_text, previous, next))