import os
import discord
from discord.ext import commands
import json
from database import get_user, create_user, save_user
from pet_system import assign_gender, level_up_check, get_language_messages

# carregar pets e languages
with open("pets.json", "r", encoding="utf8") as f:
    pets = json.load(f)

from languages import languages

intents = discord.Intents.default()
intents.message_content = True

PREFIX = "My!"
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# UTILIDADES
def get_language(user_id):
    user = get_user(user_id)
    if not user:
        return "pt"
    return user.get("lang", "pt")

def get_pet(user_id):
    user = get_user(user_id)
    if not user:
        return None
    # normalize keys to expected names
    return {
        "user_id": user["user_id"],
        "pet_species": user["pet_species"],
        "gender": user["gender"],
        "nickname": user["nickname"],
        "xp": user["xp"],
        "level": user["level"],
        "hunger": user["hunger"],
        "fun": user["fun"],
        "hygiene": user["hygiene"],
        "energy": user["energy"],
        "coins": user["coins"],
        "lang": user["lang"]
    }

def save_pet(user_id, pet_dict):
    # map pet_dict fields into DB columns
    save_user(user_id, {
        "pet_species": pet_dict.get("pet_species"),
        "gender": pet_dict.get("gender"),
        "nickname": pet_dict.get("nickname"),
        "xp": pet_dict.get("xp"),
        "level": pet_dict.get("level"),
        "hunger": pet_dict.get("hunger"),
        "fun": pet_dict.get("fun"),
        "hygiene": pet_dict.get("hygiene"),
        "energy": pet_dict.get("energy"),
        "coins": pet_dict.get("coins"),
        "lang": pet_dict.get("lang")
    })

# -------------------------------
# START: registrar pet
# -------------------------------
@bot.command()
async def start(ctx):
    user_id = ctx.author.id
    lang = get_language(user_id)
    texts = languages[lang]

    if get_user(user_id):
        return await ctx.send(texts["already_has_pet"])

    # list pets
    pet_keys = list(pets.keys())
    msg = "**Escolha seu pet:**\n\n" if lang == "pt" else "**Choose your pet:**\n\n"
    for i, key in enumerate(pet_keys):
        display = pets[key] if lang == "pt" else pets[key]
        msg += f"{i+1} — {display}\n"

    await ctx.send(msg)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

    try:
        choice_msg = await bot.wait_for("message", check=check, timeout=60.0)
    except Exception:
        return await ctx.send("Tempo esgotado. Use My!start novamente.")

    choice = int(choice_msg.content)
    if choice < 1 or choice > len(pet_keys):
        return await ctx.send(texts["choose_invalid"])

    chosen_key = pet_keys[choice - 1]
    gender = assign_gender(chosen_key)
    gender_text = languages[lang][f"gender_{gender}"]

    await ctx.send(languages[lang]["ask_nickname"] if lang == "pt" else languages[lang]["ask_nickname"])
    try:
        nick_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
    except Exception:
        return await ctx.send("Tempo esgotado. Use My!start novamente.")

    nickname = nick_msg.content.strip()[:32]

    # create user
    create_user(user_id, chosen_key, gender, nickname, lang=lang)
    await ctx.send(languages[lang]["registered"].format(nickname=nickname, pet=pets[chosen_key]))

# -------------------------------
# My!lang
# -------------------------------
@bot.command()
async def lang(ctx, language=None):
    user_id = ctx.author.id
    if language not in ["pt", "en"]:
        return await ctx.send("Idiomas disponíveis: `pt` ou `en`")
    # update DB
    save_user(user_id, {"lang": language})
    await ctx.send(languages[language]["lang_set_en"] if language == "en" else languages[language]["lang_set_pt"])

# -------------------------------
# My!help
# -------------------------------
@bot.command(name="help")
async def _help(ctx):
    lang = get_language(ctx.author.id)
    texts = languages[lang]

    embed = discord.Embed(title=texts["help_title"], description=texts["help_desc"], color=0x00ff99)
    embed.add_field(name=f"{PREFIX}start", value=texts["cmd_start"], inline=False)
    embed.add_field(name=f"{PREFIX}status", value=texts["cmd_status"], inline=False)
    embed.add_field(name=f"{PREFIX}feed", value=texts["cmd_feed"], inline=False)
    embed.add_field(name=f"{PREFIX}play", value=texts["cmd_play"], inline=False)
    embed.add_field(name=f"{PREFIX}bath", value=texts["cmd_bath"], inline=False)
    embed.add_field(name=f"{PREFIX}sleep", value=texts["cmd_sleep"], inline=False)
    embed.add_field(name=f"{PREFIX}lang", value=texts["cmd_lang"], inline=False)
    await ctx.send(embed=embed)

# -------------------------------
# My!status
# -------------------------------
@bot.command()
async def status(ctx):
    pet = get_pet(ctx.author.id)
    lang = get_language(ctx.author.id)
    texts = languages[lang]

    if not pet:
        return await ctx.send(texts["need_start"])

    embed = discord.Embed(title=f"{pet['nickname']} — Status", color=0x00aaff)
    # localize labels for PT/EN
    if lang == "pt":
        embed.add_field(name="🍗 Fome", value=f"{pet['hunger']}/100", inline=True)
        embed.add_field(name="🎾 Diversão", value=f"{pet['fun']}/100", inline=True)
        embed.add_field(name="🧼 Higiene", value=f"{pet['hygiene']}/100", inline=True)
        embed.add_field(name="😴 Energia", value=f"{pet['energy']}/100", inline=True)
        embed.add_field(name="⭐ Level", value=pet["level"], inline=True)
        embed.add_field(name="✨ XP", value=pet["xp"], inline=True)
    else:
        embed.add_field(name="🍗 Hunger", value=f"{pet['hunger']}/100", inline=True)
        embed.add_field(name="🎾 Fun", value=f"{pet['fun']}/100", inline=True)
        embed.add_field(name="🧼 Hygiene", value=f"{pet['hygiene']}/100", inline=True)
        embed.add_field(name="😴 Energy", value=f"{pet['energy']}/100", inline=True)
        embed.add_field(name="⭐ Level", value=pet["level"], inline=True)
        embed.add_field(name="✨ XP", value=pet["xp"], inline=True)

    await ctx.send(embed=embed)

# -------------------------------
# My!feed
# -------------------------------
@bot.command()
async def feed(ctx):
    user_id = ctx.author.id
    pet = get_pet(user_id)
    if not pet:
        return await ctx.send(languages["pt"]["need_start"])
    lang = get_language(user_id)
    texts = languages[lang]

    pet["hunger"] = min(100, pet["hunger"] + 20)
    save_pet(user_id, pet)
    await ctx.send(f"🍗 {pet['nickname']} {texts['fed_pet']}")

# -------------------------------
# My!play
# -------------------------------
@bot.command()
async def play(ctx):
    user_id = ctx.author.id
    pet = get_pet(user_id)
    if not pet:
        return await ctx.send(languages["pt"]["need_start"])
    lang = get_language(user_id)
    texts = languages[lang]

    pet["fun"] = min(100, pet["fun"] + 20)
    # playing costs a little energy and hunger
    pet["energy"] = max(0, pet["energy"] - 5)
    pet["hunger"] = max(0, pet["hunger"] - 5)
    save_pet(user_id, pet)
    await ctx.send(f"🎾 {pet['nickname']} {texts['played_pet']}")

# -------------------------------
# My!bath
# -------------------------------
@bot.command()
async def bath(ctx):
    user_id = ctx.author.id
    pet = get_pet(user_id)
    if not pet:
        return await ctx.send(languages["pt"]["need_start"])
    lang = get_language(user_id)
    texts = languages[lang]

    pet["hygiene"] = min(100, pet["hygiene"] + 25)
    pet["energy"] = max(0, pet["energy"] - 3)
    save_pet(user_id, pet)
    await ctx.send(f"🧼 {pet['nickname']} {texts['bath_pet']}")

# -------------------------------
# My!sleep
# -------------------------------
@bot.command()
async def sleep(ctx):
    user_id = ctx.author.id
    pet = get_pet(user_id)
    if not pet:
        return await ctx.send(languages["pt"]["need_start"])
    lang = get_language(user_id)
    texts = languages[lang]

    pet["energy"] = 100
    save_pet(user_id, pet)
    await ctx.send(f"😴 {pet['nickname']} {texts['sleep_pet']}")

# -------------------------------
# XP por mensagem (pequeno ganho)
# -------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    pet = get_pet(user_id)
    if pet:
        # ganha 1 xp por mensagem, e 1 coin ocasional
        pet["xp"] += 1
        if random_chance(10):  # 10% chance ganhar 1 coin
            pet["coins"] += 1

        leveled = level_up_check(pet)
        save_pet(user_id, pet)
        if leveled:
            lang = get_language(user_id)
            texts = languages[lang]
            # Mensagem simples de level up
            try:
                await message.channel.send(f"🎉 {pet['nickname']} subiu para o nível {pet['level']}!")
            except:
                pass

    await bot.process_commands(message)

# pequeno utilitário local
def random_chance(percent):
    return __import__("random").randint(1, 100) <= percent

# -------------------------------
# Bot run
# -------------------------------
if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("Token não encontrado. Defina a variável de ambiente TOKEN.")
    else:
        bot.run(TOKEN)