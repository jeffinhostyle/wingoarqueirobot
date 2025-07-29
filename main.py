import os
import datetime
import random
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, Dispatcher
)
from flask import Flask, request, abort

API_TOKEN = os.getenv('API_TOKEN', '7920202192:AAEGpjy5k39moDng2DpWqw_LEgmmFU-QI1U')
ADMIN_ID = 5052937721

clients = {}  # user_id: validade datetime
activation_codes = {}  # codigo: validade datetime

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def gerar_codigo_unico():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))

async def gerarcodigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para usar este comando.")
        return
    codigo = gerar_codigo_unico()
    activation_codes[codigo] = datetime.datetime.now() + datetime.timedelta(days=30)
    await update.message.reply_text(f"Código gerado: {codigo}")

async def ativar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Uso correto: /ativar <código>")
        return
    codigo = context.args[0].upper()
    validade = activation_codes.get(codigo)
    if validade and validade > datetime.datetime.now():
        clients[user_id] = validade
        del activation_codes[codigo]
        await update.message.reply_text(f"Código ativado com sucesso! Validade até {validade.strftime('%d/%m/%Y %H:%M')}")
    else:
        await update.message.reply_text("Código inválido ou expirado.")

def cliente_ativo(user_id):
    if user_id == ADMIN_ID:
        return True
    validade = clients.get(user_id)
    return validade is not None and validade > datetime.datetime.now()

async def analisar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.lower()

    if not cliente_ativo(user_id):
        await update.message.reply_text("Você não está ativado. Use /ativar <código> para ativar seu acesso.")
        return

    seq = ''.join(c for c in texto if c in ('g', 'p'))
    if len(seq) != 10:
        return

    if seq[-3:] in ('ggg', 'ppp'):
        await update.message.reply_text(
            "⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de apostar."
        )
        return

    g_count = seq.count('g')
    p_count = seq.count('p')

    if g_count > p_count:
        sinal = 'P'
    elif p_count > g_count:
        sinal = 'G'
    else:
        await update.message.reply_text(
            "⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de apostar."
        )
        return

    await update.message.reply_text(
        f"🎯 Próxima aposta: {sinal}\nUse no máximo 3 gales para otimizar suas chances.\nApós ganhar, aguarde 3 rodadas antes de apostar novamente."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bem-vindo ao bot Wingo Arqueiro!\n"
        "Admin: use /gerarcodigo para gerar códigos.\n"
        "Clientes: use /ativar <código> para ativar.\n"
        "Envie a sequência de 10 resultados (g/p) diretamente para receber seu sinal automaticamente."
    )

# Registrar handlers no dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("gerarcodigo", gerarcodigo))
dispatcher.add_handler(CommandHandler("ativar", ativar))
dispatcher.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analisar_texto))

# Rota para o webhook do Telegram
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "OK", 200
    else:
        abort(403)

# Rota raiz só para teste simples
@app.route('/')
def home():
    return "Bot está ativo!", 200

if __name__ == '__main__':
    # Configurar webhook para seu domínio Railway (substitua abaixo pelo seu domínio)
    webhook_url = f'https://web-production-d7eba.up.railway.app/{API_TOKEN}'
    bot.delete_webhook()
    bot.set_webhook(url=webhook_url)

    # Rodar app Flask (Gunicorn deve ser usado no Railway)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
