import discord
from discord.ext import commands
import os
import json
from datetime import datetime, timedelta
# Importamos o módulo Keep-Alive para evitar que o Heroku suspenda o bot
from keep_alive import keep_alive 

# --- CONFIGURAÇÃO INICIAL E PERSISTÊNCIA DE DADOS ---
PREFIX = "My!"
# O Token será lido da variável de ambiente (Config Vars do Heroku)
TOKEN = os.getenv("TOKEN") 
DATA_FILE = "data.json" 
COOLDOWN_DAILY_HOURS = 24
MYCOINS_DAILY = 50

# --- PETS E TRADUÇÕES ---
PETS = ["Gato", "Cachorro", "Dinossauro", "Dragão", "Alienígena", "Peixe"]

TRADS = {
    'en': {
        'pet_not_chosen': "You haven't chosen a pet yet! Use `My!start` to choose one.",
        'daily_success': "Here are your {coins} Mycoins! Come back in {hours} hours.",
        'daily_cooldown': "You already claimed your daily reward. Try again in {time_left}.",
        'lang_set': "Language set to English.",
        'pet_start': "Welcome, {pet}! You chose the {pet_type}. Let the adventure begin!",
        'pet_already': "You already have a pet: {pet_type}. You can't choose another one.",
        'start_msg': "Welcome! Use `My!start <pet_name>` to choose one: {pets_list}",
        'level_up': "🎉 **{user}**, your pet **{pet_name}** leveled up to **level {level}**!",
    },
    'pt': {
        'pet_not_chosen': "Você ainda não escolheu um pet! Use `My!start` para escolher um.",
        'daily_success': "Aqui estão suas {coins} Mycoins! Volte em {hours} horas.",
        'daily_cooldown': "Você já pegou sua recompensa diária. Tente novamente em {time_left}.",
        'lang_set': "Idioma definido para Português.",
        'pet_start': "Bem-vindo(a), {pet}! Você escolheu o(a) {pet_type}. Que a aventura comece!",
        'pet_already': "Você já tem um pet: {pet_type}. Você não pode escolher outro.",
        'start_msg': "Boas-vindas! Use `My!start <nome_do_pet>` para escolher um: {pets_list}",
        'level_up': "🎉 **{user}**, seu pet **{pet_name}** subiu para o **nível {level}**!",
    }
}

# --- FUNÇÕES DE PERSISTÊNCIA E TRADUÇÃO (Inalteradas) ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

user_data = load_data()

def get_lang(user_id):
    return user_data.get(str(user_id), {}).get('lang', 'pt') 

def get_trad(user_id, key, **kwargs):
    lang = get_lang(user_id)
    text = TRADS.get(lang, TRADS['pt']).get(key, "TEXT NOT FOUND") 
    return text.format(**kwargs)

# --- CONFIGURAÇÃO DO BOT ---
intents = discord.Intents.default()
intents.message_content = True 
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- EVENTOS ---

@bot.event
async def on_ready():
    print(f'Bot Myra conectado como {bot.user.name}')
    # INICIA O SERVIDOR WEB PARA MONITORAMENTO
    keep_alive()

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    user_id = str(message.author.id)
    
    # Lógica de XP por mensagem
    if user_id in user_data and user_data[user_id].get('pet') and not message.content.startswith(PREFIX):
        user_data[user_id].setdefault('xp', 0)
        user_data[user_id].setdefault('level', 1)
        user_data[user_id]['xp'] += 1 
        
        if user_data[user_id]['xp'] >= user_data[user_id]['level'] * 10:
             user_data[user_id]['xp'] = 0
             user_data[user_id]['level'] += 1
             pet_name = user_data[user_id]['pet']
             level = user_data[user_id]['level']
             await message.channel.send(
                 get_trad(user_id, 'level_up', user=message.author.name, pet_name=pet_name, level=level)
             )
        save_data(user_data)
    await bot.process_commands(message)

# --- COMANDOS (Os comandos estão todos aqui) ---

@bot.command(name='start', aliases=['iniciar'])
async def start_pet(ctx, pet_choice=None):
    user_id = str(ctx.author.id)
    if user_id in user_data and user_data[user_id].get('pet'):
        pet_type = user_data[user_id]['pet']
        await ctx.send(get_trad(user_id, 'pet_already', pet_type=pet_type))
        return
    if not pet_choice or pet_choice.capitalize() not in PETS:
        pets_list = ", ".join(PETS)
        await ctx.send(get_trad(user_id, 'start_msg', pets_list=pets_list))
        return
    chosen_pet = pet_choice.capitalize()
    user_data[user_id] = {
        'pet': chosen_pet, 'xp': 0, 'level': 1, 'mycoins': 10, 'last_daily': None,
        'lang': get_lang(user_id), 
        'status': {'fome': 100, 'felicidade': 100, 'energia': 100}
    }
    save_data(user_data)
    await ctx.send(get_trad(user_id, 'pet_start', pet=ctx.author.name, pet_type=chosen_pet))

@bot.command(name='lang', aliases=['idioma'])
async def set_language(ctx, language=None):
    user_id = str(ctx.author.id)
    valid_langs = ['pt', 'en']
    if not language or language.lower() not in valid_langs:
        await ctx.send(f"Use: `{PREFIX}lang pt` ou `{PREFIX}lang en`")
        return
    new_lang = language.lower()
    user_data.setdefault(user_id, {})
    user_data[user_id]['lang'] = new_lang
    save_data(user_data)
    await ctx.send(get_trad(user_id, 'lang_set'))

@bot.command(name='daily', aliases=['diario'])
async def daily_reward(ctx):
    user_id = str(ctx.author.id)
    if user_id not in user_data or not user_data[user_id].get('pet'):
        await ctx.send(get_trad(user_id, 'pet_not_chosen'))
        return
    last_daily_str = user_data[user_id].get('last_daily')
    now = datetime.now()
    if last_daily_str:
        last_daily = datetime.strptime(last_daily_str, '%Y-%m-%d %H:%M:%S.%f')
        next_claim_time = last_daily + timedelta(hours=COOLDOWN_DAILY_HOURS)
        time_left = next_claim_time - now
        if time_left.total_seconds() > 0:
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            time_str = f"{hours}h e {minutes}min"
            await ctx.send(get_trad(user_id, 'daily_cooldown', time_left=time_str))
            return
    user_data[user_id]['mycoins'] = user_data[user_id].get('mycoins', 0) + MYCOINS_DAILY
    user_data[user_id]['last_daily'] = str(now)
    save_data(user_data)
    await ctx.send(get_trad(user_id, 'daily_success', coins=MYCOINS_DAILY, hours=COOLDOWN_DAILY_HOURS))

@bot.command(name='help', aliases=['ajuda'])
async def help_command(ctx):
    embed = discord.Embed(
        title="Ajuda do Myra Bot", description="Um pet virtual no seu Discord! Prefix: `My!`", color=0x833AB4)
    embed.add_field(name="🐾 Comandos de Pet", value="`My!start <pet>`: Escolhe seu primeiro pet.\n(Pets: Gato, Cachorro, Dinossauro, Dragão, Alienígena, Peixe)", inline=False)
    embed.add_field(name="💰 Comandos de Moedas", value="`My!daily`: Recebe sua recompensa diária de Mycoins.", inline=False)
    embed.add_field(name="⚙️ Configuração", value="`My!lang <pt/en>`: Define o idioma do bot para você.", inline=False)
    embed.set_footer(text="Lembre-se: seu pet ganha XP a cada mensagem que você envia!")
    await ctx.send(embed=embed)


# --- EXECUÇÃO DO BOT ---
if TOKEN is None:
    print("ERRO: O Token do Bot não foi encontrado na variável de ambiente 'TOKEN'.")
else:
    bot.run(TOKEN)
