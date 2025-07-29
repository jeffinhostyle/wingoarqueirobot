import os
import datetime
import random
import asyncio
from flask import Flask, request, abort
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters
)

API_TOKEN = os.getenv('API_TOKEN', '').strip()
if not API_TOKEN:
    raise ValueError("API_TOKEN não configurado ou está vazio!")

ADMIN_ID = 5052937721

clients = {}  # user_id: validade datetime
activation_codes = {}  # codigo: validade datetime

app = Flask(__name__)
bot = Bot(token=API_TOKEN)

application = Application.builder().token(API_TOKEN).build()

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

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("gerarcodigo", gerarcodigo))
application.add_handler(CommandHandler("ativar", ativar))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analisar_texto))

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot está ativo!', 200

async def setup_webhook():
    webhook_url = f'https://web-production-d7eba.up.railway.app/{API_TOKEN}'
    print(f"Webhook URL configurada para: {webhook_url}")
    await bot.delete_webhook()
    await bot.set_webhook(url=webhook_url)

if __name__ == '__main__':
    asyncio.run(setup_webhook())
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
