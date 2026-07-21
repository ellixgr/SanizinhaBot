import os
import uuid
import requests
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "SanizinhaBot está online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

TELEGRAM_TOKEN = "8634433708:AAGH67_iFaiMDHHPOVBQUx_GpxOlM-Lu97c"
MP_ACCESS_TOKEN = "APP_USR-4578357640781383-101515-089e854df4cde17d09a4e28316782210-2028678149"
LINK_DO_PRODUTO = "https://ellixgr.github.io/flow/"
VALOR_PRODUTO = 10.00

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Comprar Acesso (PIX)", callback_data="comprar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Olá! Seja bem-vindo ao SanizinhaBot.\n\nClique no botão abaixo para gerar o seu PIX e liberar o seu acesso instantaneamente:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    if query.data == "comprar":
        try:
            await query.edit_message_text("⏳ Gerando seu PIX, aguarde um instante...")
        except Exception:
            pass

        user = update.effective_user
        nome = user.first_name if user.first_name else "Cliente"
        sobrenome = user.last_name if user.last_name else "Telegram"

        url = "https://api.mercadopago.com/v1/payments"
        
        # CHAVE IDEMPOTENCY OBRIGATÓRIA ADICIONADA AQUI
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4())
        }
        
        payload = {
            "transaction_amount": VALOR_PRODUTO,
            "description": "Acesso VIP",
            "payment_method_id": "pix",
            "payer": {
                "email": f"user_{user.id}@telegrambot.com",
                "first_name": nome,
                "last_name": sobrenome
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            payment_id = data["id"]
            point_of_interaction = data.get("point_of_interaction", {})
            qr_data = point_of_interaction.get("transaction_data", {}).get("qr_code", "")
            
            msg = (
                "✅ **PIX Gerado com Sucesso!**\n\n"
                f"💰 **Valor:** R$ {VALOR_PRODUTO:.2f}\n\n"
                "📋 **Copie e cole o código PIX abaixo:**\n"
                f"`{qr_data}`\n\n"
                "⏳ *Assim que você pagar, clique no botão abaixo para confirmar.*"
            )
            
            keyboard = [[InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_{payment_id}")]]
            await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            erro_mp = response.text[:300]
            print("Erro Mercado Pago:", response.text)
            await query.message.reply_text(f"❌ Erro do Mercado Pago:\n`{erro_mp}`", parse_mode="Markdown")

    elif query.data.startswith("check_"):
        payment_id = query.data.split("_")[1]
        
        url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            
            if status == "approved":
                await query.message.reply_text(
                    f"🎉 **Pagamento Aprovado com Sucesso!**\n\n"
                    f"Muito obrigado pela compra. Aqui está o seu link de acesso:\n{LINK_DO_PRODUTO}"
                )
            else:
                await query.answer("❌ O pagamento ainda não foi identificado. Pague o Pix e tente novamente em instantes!", show_alert=True)
        else:
            await query.answer("❌ Erro ao verificar pagamento. Tente novamente.", show_alert=True)

def main():
    t = threading.Thread(target=run_web)
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot do Telegram rodando...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
