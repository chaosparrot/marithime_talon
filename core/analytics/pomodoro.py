from talon import Context, Module, cron, speech_system, settings, actions
import random

eyestrain_messages = [
    "Is it raining outside?",
    "Imagine looking at advertisements lmao",
    "Are the plants okay?",
    "Flashbang!",
    "Screen isn't going anywhere",
]

hydration_messages = [
    "Drink!",
    "Water you waiting for?",
    "Thirsty yet?",
    "Coffee isn't water",
    "Dehydration warning!",
    "Kidney strike!",
    "Kidney stone unlocked!",
    "Dehydrate the planet!"
]

pomodoro_messages = [
    "Touch grass nerd!",
    "Your body demands stretches!",
    "Relax your shoulders",
    "Tension isn't needed in this scenario",
    "Walk downstairs and back up again", 
    "Breathe damn it, breathe!",
    "Get to tha choppah",
    "Duck and cover",
    "Wiggle wiggle wiggle",    
]

def health_check():
    actions.user.hud_add_log("success", random.choice(pomodoro_messages))
    
def hydrate_check():
    actions.user.hud_add_log("event", random.choice(hydration_messages))
    
def eyestrain_check():
    actions.user.hud_add_log("error", random.choice(eyestrain_messages))

# Every 10 minutes, or 60 * 10 seconds, give an eyestrain message
cron.interval("600s", eyestrain_check)

# Every 20 minutes, or 60 * 20 seconds, give a stretching message
cron.interval("1200s", health_check)

# Every 30 minutes, or 60 * 30 seconds, give a hydration message
cron.interval("1800s", hydrate_check)