import random
from languages import languages

MAX_STAT = 100
LEVEL_CAP = 1000

def assign_gender(pet_key):
    if pet_key == "alien":
        return "neutral"
    return random.choice(["male", "female"])

def level_up_check(user):
    # leveling rule: required xp = level * 10 (progressive)
    # keeps cap at LEVEL_CAP
    if user["level"] >= LEVEL_CAP:
        return False
    required = user["level"] * 10
    if user["xp"] >= required:
        user["level"] += 1
        user["xp"] = 0
        return True
    return False

def get_language_messages(lang_code):
    return languages.get(lang_code, languages["pt"])