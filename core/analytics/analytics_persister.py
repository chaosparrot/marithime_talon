from talon import Context, Module, cron, speech_system, actions
from typing import List
import os
from datetime import datetime, timedelta
from time import time
import re

# Create a folder for the phrase and keystroke data
data_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
if not os.path.isdir(data_folder):
    os.mkdir(data_folder)

mod = Module()
class AnalyticsPersister:
    phrase_buffer: List[str]
    keystroke_buffer: List[str]
    skip_keystrokes = 0
    
    def __init__(self):
        self.phrase_buffer = []
        self.keystroke_buffer = []

        # Every 60 seconds, persist the buffers that are filled for the analytics
        cron.interval("60s", lambda self=self: self.persist_buffers())
        
        # Register every phrase
        speech_system.register("post:phrase", self.append_phrase)

    def get_current_phrases_file(self):
        return os.path.join(data_folder, "phrases_" + datetime.now().strftime("%Y-%m-%d") + ".csv")
        
    def get_current_keystrokes_file(self):
        return os.path.join(data_folder, "keystrokes_" + datetime.now().strftime("%Y-%m-%d") + ".csv")

    def append_phrase(self, phrase):
        word_list = phrase["phrase"]
        command = " ".join(word.split("\\")[0] for word in word_list)    
        self.phrase_buffer.append(command)
        
    def split_keystrokes(self, keystroke_string: str) -> List[str]:
        total_keystrokes = []

        split_keystrokes = re.split(' |-', keystroke_string)
        for keystroke in split_keystrokes:
            # Skip key releases from being logged
            if ":up" not in split_keystrokes:
                keystroke_parts = keystroke.split(":")
                if len(keystroke_parts) > 1 and keystroke_parts[1].isnumeric():
                    total_keystrokes.extend([keystroke_parts[0]] * (int(keystroke_parts[1]) - 1))

                if len(keystroke_parts) > 0:
                    total_keystrokes.append(keystroke_parts[0])
        return total_keystrokes
        
    def split_insert(self, insert_string: str) -> List[str]:
        space_symbols = "~`\"'^"
        shift_symbols = "#$%&*()_+{}:|<>?"
        shift_down = False
        keystrokes = []
        for char in insert_string:
            is_uppercase = char.isupper() or char in shift_symbols
            if is_uppercase and shift_down == False:
                keystrokes.append("shift")

            keystrokes.append(char.lower() if char != " " else "space")
            if char in space_symbols:
                keystrokes.append("space")
            
            # In case we are dealing with spaces or other elements
            # While the previous character was an uppercase character
            # Keep assuming that the shift should be pressed down
            if not is_uppercase and shift_down == True and char in " `'":
                is_uppercase = True
            shift_down = is_uppercase
        return keystrokes

    def append_keystroke(self, keystrokes: str):
        # Skip upper case keystrokes as they are implemented by inserts already
        if self.skip_keystrokes > 0:
            self.skip_keystrokes -= 1
        else:
            self.skip_keystrokes = 0
            self.keystroke_buffer.append(keystrokes)

    def append_insert(self, insert_string: str):
        keystrokes = self.split_insert(insert_string)
        self.keystroke_buffer.extend(keystrokes)
        self.skip_keystrokes += len(keystrokes)

    def persist_buffers(self):
        phrases_filename = self.get_current_phrases_file()
        keystrokes_filename = self.get_current_keystrokes_file()
        timestamp = str(int(time()))

        # Always persist the buffer of phrases said
        phrase_buffer_string = ""    
        if len(self.phrase_buffer) > 0:
            for phrase in self.phrase_buffer:
                phrase_buffer_string += timestamp + ';"' + phrase.replace('"', '\"') + '"\n'
        else:
            phrase_buffer_string += timestamp + ';NO ACTIVITY\n'
        with open(phrases_filename, "a") as phrases_file:
            phrases_file.write(phrase_buffer_string)
        self.phrase_buffer = []

        if len(self.keystroke_buffer) > 0:
            keystroke_buffer_count = []
            for keystrokes in self.keystroke_buffer:
                split_keystroke_list = self.split_keystrokes( keystrokes )
                keystroke_buffer_count.extend(split_keystroke_list)
            with open(keystrokes_filename, "a") as keystrokes_file:
                keystrokes_file.write(timestamp + ';' + str(len(keystroke_buffer_count)) + '\n')
        self.keystroke_buffer = []
    
    def show_statistics(self, average_daily_keystrokes: int = 16350):
        keystrokes_filename = self.get_current_keystrokes_file()
        keystrokes_today = 0
        with open(keystrokes_filename, "r") as keystroke_file:
            lines = keystroke_file.readlines()
            for line in lines:
                keystrokes_today += int(line.split(";")[1])
        
        keystrokes_percent = (keystrokes_today / average_daily_keystrokes) * 100
        text = "<*Today/>\n\n"
        text += "Keystrokes saved: " + str(keystrokes_today) + "\n"

        text += str("%.1f" % (keystrokes_percent)) + "% of avg. usage\n\n"
        
        # Get the last weeks statistics
        statistics = {}
        keystroke_files = [x for x in os.listdir(data_folder) if x.endswith(".csv") and x.startswith("keystrokes_")]
        for file in keystroke_files:
            datetime_string = file.replace("keystrokes_", "").replace(".csv", "")
            date_obj = datetime.strptime(datetime_string, "%Y-%m-%d")
            if (datetime.now() - date_obj).days < 7:
                file_location = os.path.join(data_folder, file)

                keystrokes_daily = 0
                with open(file_location, "r") as keystroke_file:
                    lines = keystroke_file.readlines()
                    for line in lines:
                        keystrokes_daily += int(line.split(";")[1])
                
                statistics[datetime_string] = {
                    "keystrokes": keystrokes_daily,
                    "keystrokes_percent":  (keystrokes_daily / average_daily_keystrokes) * 100
                }
        
        text = ""
        reverse_chronological_dates = list(statistics.keys())
        reverse_chronological_dates.reverse()
        for logged_date in reverse_chronological_dates:
            datename = logged_date
            if logged_date == datetime.now().strftime("%Y-%m-%d"):
                datename = "Today"
            if logged_date == ( datetime.now() - timedelta(days=1) ).strftime("%Y-%m-%d"):
                datename = "Yesterday"
            
            text += "<*" + datename + "/>\n\n"
            text += "Keystrokes saved: " + str(statistics[logged_date]["keystrokes"]) + "\n"
            if statistics[logged_date]["keystrokes_percent"] > 30:
                text += "<*<+"
            elif statistics[logged_date]["keystrokes_percent"] > 10:
                text += "<*<!"
            else:
                text += "<*<!!"

            text += str("%.1f" % (statistics[logged_date]["keystrokes_percent"])) + "%/>/> of avg. usage\n\n"

        actions.user.hud_publish_content(text, "talon_analytics", "Usage analytics")

analytics_persister = AnalyticsPersister()

@mod.action_class
class AnalyticsActions:

    def append_insert_to_analytics(insert_string: str):
        """Append a series of key presses in the form of a typed string to the analytics files"""
        global analytics_persister
        analytics_persister.append_insert(insert_string)
    
    def append_keystroke_to_analytics(keystroke: str):
        """Append a key stroke to the analytics files"""    
        global analytics_persister
        analytics_persister.append_keystroke(keystroke)

    def analytics_show_statistics():
        """Show the statistics of keystrokes and speech handled by Talon"""
        global analytics_persister
        analytics_persister.show_statistics()

