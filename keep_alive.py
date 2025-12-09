import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    # Mensagem que o UptimeRobot irá ver.
    return "O bot Myra está online e rodando no Heroku! 🚀"

def run():
  # O Heroku define a porta que o servidor deve usar usando a variável de ambiente PORT.
  port = int(os.environ.get("PORT", 5000))
  app.run(host='0.0.0.0', port=port) 

def keep_alive():
  '''Inicia o servidor web em uma thread separada para não bloquear o bot.'''
  t = Thread(target=run)
  t.start()
