import os
import datetime
import random
import asyncio

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from flask import Flask, request

API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise RuntimeError("Variável de ambiente API_TOKEN não encontrada!")

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
if not WEBHOOK_URL:
    raise RuntimeError("Variável de ambiente WEBHOOK_URL não encontrada!")

ADMIN_ID = 5052937721

clients = {}         # {user_id: validade_datetime}
activation_codes = {}  # {codigo: validade_datetime}

app = Flask(__name__)
bot = Bot(token=API_TOKEN)

async def gerarcodigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Você não tem permissão para usar este comando.")
        return
    codigo = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))
    validade = datetime.datetime.now() + datetime.timedelta(days=30)
    activation_codes[codigo] = validade
    await update.message.reply_text(f"✅ Código gerado: {codigo}\nValidade até {validade.strftime('%d/%m/%Y %H:%M')}")

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
        await update.message.reply_text(f"✅ Ativação feita com sucesso! Validade até {validade.strftime('%d/%m/%Y %H:%M')}")
    else:
        await update.message.reply_text("❌ Código inválido ou expirado.")

def cliente_ativo(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    validade = clients.get(user_id)
    return validade is not None and validade > datetime.datetime.now()

async def analisar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.lower()

    if not cliente_ativo(user_id):
        await update.message.reply_text("❌ Você não está ativado. Use /ativar <código> para ativar o acesso.")
        return

    seq = ''.join(c for c in texto if c in ('g', 'p'))
    if len(seq) != 10:
        return

    if seq[-3:] in ('ggg', 'ppp'):
        await update.message.reply_text(
            "⚠️ Padrão desfavorável detectado.\nPor segurança, aguarde 3 rodadas antes de apostar."
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
            "⚠️ Padrão desfavorável detectado.\nPor segurança, aguarde 3 rodadas antes de apostar."
        )
        return

    await update.message.reply_text(
        f"🎯 Próxima aposta: {sinal}\nUse no máximo 3 gales.\nApós ganhar, aguarde 3 rodadas antes de apostar novamente."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bem-vindo ao Bot Wingo Arqueiro!\n\n"
        "Admin: /gerarcodigo para gerar códigos.\n"
        "Cliente: /ativar <código> para ativar seu acesso.\n"
        "Envie uma sequência de 10 resultados (g/p) para receber seu sinal automático."
    )

application = ApplicationBuilder().token(API_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("gerarcodigo", gerarcodigo))
application.add_handler(CommandHandler("ativar", ativar))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analisar_texto))

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return "OK", 200

@app.route('/')
def index():
    return "Bot Wingo Arqueiro está ativo!", 200

async def setup_webhook():
    webhook_url = f"{WEBHOOK_URL}/{API_TOKEN}"
    await bot.delete_webhook()
    await bot.set_webhook(webhook_url)
    print(f"Webhook configurado para: {webhook_url}")

if __name__ == '__main__':
    asyncio.run(setup_webhook())
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')))
