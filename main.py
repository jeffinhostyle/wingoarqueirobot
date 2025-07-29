import os
import telebot
from flask import Flask, request

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

def analisar_resultados(resultados):
    padrao = ''.join(resultados[-3:])
    if padrao == 'GGG':
        return 'Entrar no PRETO - Gale 1'
    elif padrao == 'PPP':
        return 'Entrar no VERMELHO - Gale 1'
    else:
        return 'Aguardar novo sinal.'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Olá! Envie os últimos 10 resultados da roleta (com G ou P) e eu te digo a melhor entrada!")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    texto = message.text.upper().replace(" ", "")
    if all(c in "GP" for c in texto) and 8 <= len(texto) <= 12:
        sugestao = analisar_resultados(list(texto)[-10:])
        bot.reply_to(message, f"📊 Análise feita!\nSugestão: {sugestao}")
    else:
        bot.reply_to(message, "Envie os últimos 10 resultados usando apenas G (vermelho) e P (preto).")

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot está ativo!', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv('WEBHOOK_URL'))
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
