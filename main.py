import os
import datetime
import random
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from flask import Flask, request

API_TOKEN = os.getenv('API_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

if not API_TOKEN:
    raise ValueError("API_TOKEN não configurado!")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL não configurado!")

WEBHOOK_URL = WEBHOOK_URL.strip()

print(f"[LOG] WEBHOOK_URL usado: '{WEBHOOK_URL}'")

ADMIN_ID = 5052937721
clients = {}
activation_codes = {}

app = Flask(__name__)
application = ApplicationBuilder().token(API_TOKEN).build()

def gerar_codigo_unico():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))

async def gerarcodigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Sem permissão para esse comando.")
        return
    codigo = gerar_codigo_unico()
    activation_codes[codigo] = datetime.datetime.now() + datetime.timedelta(days=30)
    await update.message.reply_text(f"Código gerado: {codigo}")

async def ativar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Uso correto: /ativar <código>")
        return
    codigo = context.args[0].upper()
    validade = activation_codes.get(codigo)
    if validade and validade > datetime.datetime.now():
        clients[update.effective_user.id] = validade
        del activation_codes[codigo]
        await update.message.reply_text(f"Ativado até {validade.strftime('%d/%m/%Y %H:%M')}")
    else:
        await update.message.reply_text("Código inválido ou expirado.")

def cliente_ativo(user_id):
    if user_id == ADMIN_ID:
        return True
    validade = clients.get(user_id)
    return validade and validade > datetime.datetime.now()

async def analisar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cliente_ativo(update.effective_user.id):
        await update.message.reply_text("Use /ativar <código> para ativar seu acesso.")
        return

    texto = update.message.text.lower()
    seq = ''.join(c for c in texto if c in ('g', 'p'))
    if len(seq) != 10:
        return

    if seq[-3:] in ('ggg', 'ppp'):
        await update.message.reply_text(
            "⚠️ Padrão desfavorável. Aguarde 3 rodadas antes de apostar."
        )
        return

    g_count = seq.count('g')
    p_count = seq.count('p')
    sinal = 'P' if g_count > p_count else 'G' if p_count > g_count else None

    if not sinal:
        await update.message.reply_text(
            "⚠️ Padrão desfavorável. Aguarde 3 rodadas antes de apostar."
        )
        return

    await update.message.reply_text(
        f"🎯 Próxima aposta: {sinal}\nUse até 3 gales.\nApós ganhar, aguarde 3 rodadas."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot Wingo Arqueiro\n"
        "Admin: /gerarcodigo\n"
        "Cliente: /ativar <código>\n"
        "Envie sequência de 10 resultados (g/p) para receber sinal."
    )

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("gerarcodigo", gerarcodigo))
application.add_handler(CommandHandler("ativar", ativar))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analisar_texto))

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200

@app.route("/")
def index():
    return "Bot rodando."

async def set_webhook():
    print("[LOG] Configurando webhook...")
    await application.bot.delete_webhook()
    await application.bot.set_webhook(WEBHOOK_URL)
    print("[LOG] Webhook configurado.")

if __name__ == "__main__":
    import threading
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
