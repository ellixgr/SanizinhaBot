import os
import uuid
import random
import time
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

# CONFIGURAÇÕES DO BOT E MERCADO PAGO
TELEGRAM_TOKEN = "8634433708:AAGH67_iFaiMDHHPOVBQUx_GpxOlM-Lu97c"
MP_ACCESS_TOKEN = "APP_USR-4578357640781383-101515-089e854df4cde17d09a4e28316782210-2028678149"
LINK_DO_GRUPO = "https://t.me/+ZWUMQ-KbutpkY2Yx"

# LISTA DE VÍDEOS PARA ENVIO ALEATÓRIO NO START
VIDEOS_START = [
    "https://ellixgr.github.io/x23wzp/VID_20260713_133754_437.mp4",
    "https://ellixgr.github.io/x23wzp/1783749549965.mp4",
    "https://ellixgr.github.io/x23wzp/1783749723785.mp4"
]

# CONTROLE DE ANTI-FLOOD (Bloqueia por 5 minutos se floodar)
user_cooldowns = {}
user_bans = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    agora = time.time()

    # Verifica se o usuário está bloqueado temporariamente por flood (5 minutos)
    if user_id in user_bans:
        tempo_restante = user_bans[user_id] - agora
        if tempo_restante > 0:
            return # Ignora totalmente para proteger o bot contra ban/flood
        else:
            del user_bans[user_id]

    # Controle de intervalo rápido (Anti-Spam de cliques)
    if user_id in user_cooldowns and (agora - user_cooldowns[user_id]) < 5:
        user_bans[user_id] = agora + 300 # Bloqueia por 5 minutos
        return
    user_cooldowns[user_id] = agora

    # Texto de boas-vindas solicitado
    texto_boas_vindas = (
        "🔥 𝗦𝗘𝗝𝗔 𝗕𝗘𝗠-𝗩𝗜𝗡𝗗𝗢 𝗔𝗢 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗢 𝗗𝗔𝗦 𝗙𝗔𝗩𝗘𝗟𝗔𝗗𝗜𝗡𝗛𝗔𝗦 𝗚𝗢𝗦𝗧𝗢𝗦𝗔𝗦 🇧🇷\n\n"
        "🇧🇷 𝙁𝙖𝙫𝙚𝙡𝙖𝙙𝙞𝙣𝙝𝙖𝙨, 𝙙𝙚𝙨𝙚𝙨𝙥𝙚𝙧𝙖𝙙𝙖𝙨, 𝙣𝙞𝙣𝙛𝙚𝙩𝙖𝙨 𝙙𝙖 𝙘𝙖𝙨𝙖 𝙨𝙚𝙢 𝙧𝙚𝙗𝙤𝙘𝙤, 𝙢𝙖𝙜𝙧𝙞𝙣𝙝𝙖𝙨 𝙥𝙚𝙞𝙩𝙪𝙙𝙖𝙨, 𝙩𝙪𝙙𝙤 𝙚𝙢 1 𝙂𝙍𝙐𝙋𝙊 😈\n\n"
        "🥵 Aqui é só material BRUTO e sem censura:\n\n"
        "🔥 +130 mil mídias (videos e fotos)\n\n"
        "🔥 𝐏𝐨𝐛𝐫𝐢𝐧𝐡𝐚𝐬 𝐭𝐚𝐫𝐚𝐝𝐚𝐬 𝐪𝐮𝐞 𝐧ã𝐨 𝐭𝐞𝐦 𝐥𝐢𝐦𝐢𝐭𝐞\n"
        "🔥 𝐄𝐬𝐩𝐨𝐬𝐚𝐬 𝐭𝐫𝐚𝐢𝐧𝐝𝐨 𝐨 𝐦𝐚𝐫𝐢𝐝𝐨 𝐬𝐨 𝐩𝐞𝐥𝐚 𝐞𝐦𝐨çã𝐨\n"
        "🔥 𝐍𝐨𝐯𝐢𝐧𝐡𝐚𝐬⁺¹⁸ 𝐝𝐚 𝐩𝐞𝐫𝐢𝐟𝐞𝐫𝐢𝐚 𝐪𝐮𝐞 𝐚𝐝𝐨𝐫𝐚𝐦 𝐮𝐦𝐚 𝐬𝐚𝐜𝐚𝐧𝐚𝐠𝐞𝐦 𝐧𝐨 𝐬𝐢𝐠𝐢𝐥𝐨\n"
        "🔥 𝐆𝐨𝐬𝐭𝐨𝐬𝐚𝐬 𝐝𝐨 𝐛𝐚𝐫𝐫𝐚𝐜𝐨 𝐟𝐚𝐳𝐞𝐧𝐝𝐨 𝐭𝐮𝐝𝐨 𝐩𝐨𝐫 𝐝𝐢𝐯𝐞𝐫𝐬ã𝐨\n"
        "🔥 𝐍𝐢𝐧𝐟𝐞𝐭𝐚𝐬 𝐜𝐨𝐦 𝐦𝐚𝐫𝐪𝐮𝐢𝐧𝐡𝐚 𝐝𝐞 𝐟𝐢𝐭𝐚\n"
        "🔥 𝐏𝐚𝐝𝐫𝐚𝐬𝐭𝐫𝐨 𝐜𝐨𝐦𝐞𝐧𝐝𝐨 𝐍𝐨𝐯𝐢𝐧𝐡𝐚⁺¹⁸\n"
        "🔥 𝐋𝟑𝐢𝐭𝐢𝐧𝐡𝟎 𝐧𝐚 𝐛𝐨𝐜𝐚 𝐝𝐚 𝐓𝐢𝐭𝐢𝐚⁺¹⁸\n"
        "🔥 𝐍𝐨𝐯𝐢𝐧𝐡𝐚𝐬⁺¹⁸ 𝐬𝐞 𝐞𝐱𝐢𝐛𝐢𝐧𝐝𝐨 𝐩𝐨𝐫 𝐝𝐢𝐧𝐡𝐞𝐢𝐫𝐨\n"
        "🔥 𝐍𝐨𝐯𝐢𝐧𝐡𝐚𝐬⁺¹⁸ 𝐩𝐨𝐛𝐫𝐞 𝐪𝐮𝐞 𝐧𝐚𝐨 𝐭𝐞𝐦 𝐟𝐫𝐞𝐬𝐜𝐮𝐫𝐚\n\n"
        "👇 Escolha o seu plano abaixo:"
    )

    # Botões com os valores solicitados
    keyboard = [
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐒𝐄𝐌𝐀𝐍𝐀 → R$ 7,00", callback_data="comprar_7.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐌𝐄𝐒 → R$ 20,00", callback_data="comprar_20.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐄𝐑𝐌𝐀𝐍𝐄𝐍𝐓𝐄 → R$ 60,00", callback_data="comprar_60.00")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Escolhe um vídeo aleatório da lista
    video_escolhido = random.choice(VIDEOS_START)

    try:
        await update.message.reply_video(
            video=video_escolhido,
            caption=texto_boas_vindas,
            reply_markup=reply_markup
        )
    except Exception:
        # Fallback caso dê erro no envio do vídeo por instabilidade da URL
        await update.message.reply_text(texto_boas_vindas, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data

    if data.startswith("comprar_"):
        valor = float(data.split("_")[1])
        
        try:
            await query.edit_message_caption(caption="⏳ Gerando seu PIX, aguarde um instante...", reply_markup=None)
        except Exception:
            try:
                await query.edit_message_text("⏳ Gerando seu PIX, aguarde um instante...")
            except Exception:
                pass

        user = update.effective_user
        nome = user.first_name if user.first_name else "Cliente"
        sobrenome = user.last_name if user.last_name else "Telegram"

        url = "https://api.mercadopago.com/v1/payments"
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4())
        }
        payload = {
            "transaction_amount": valor,
            "description": f"Acesso VIP - R$ {valor:.2f}",
            "payment_method_id": "pix",
            "payer": {
                "email": f"user_{user.id}@telegrambot.com",
                "first_name": nome,
                "last_name": sobrenome
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            resp_data = response.json()
            payment_id = resp_data["id"]
            qr_data = resp_data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
            
            msg = (
                f"✅ **PIX Gerado com Sucesso!**\n\n"
                f"💰 **Valor:** R$ {valor:.2f}\n\n"
                "👇 *Clique no botão abaixo para copiar a chave Pix automaticamente:*"
            )
            
            # Botão com a chave Pix embutida (url com scheme 'copy' ou o próprio código no callback / botão de URL se suportado, 
            # como o Telegram aceita URL type nos botões inline, podemos usar um truque de callback com alerta ou botões lado a lado)
            keyboard = [
                [InlineKeyboardButton("📋 Copiar Chave Pix", url=f"https://api.whatsapp.com/send?text={qr_data}")], # Atalho seguro ou instrução clara
                [InlineKeyboardButton("🔄 Verificar se Já Paguei", callback_data=f"check_{payment_id}")]
            ]
            
            # Nota: Como o Telegram não permite copiar texto direto por botão de callback padrão sem abrir link, 
            # vamos mandar o código em bloco de código para facilitar o toque e colocar o botão de verificação logo abaixo:
            msg_completa = (
                f"✅ **PIX Gerado com Sucesso!**\n\n"
                f"💰 **Valor:** R$ {valor:.2f}\n\n"
                "📋 **Copie o código abaixo (toque em cima para copiar):**\n"
                f"`{qr_data}`\n\n"
                "⏳ *Após pagar, clique no botão abaixo para liberar seu acesso instantaneamente!*"
            )

            keyboard_final = [
                [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_{payment_id}")]
            ]

            await query.message.reply_text(msg_completa, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard_final))
        else:
            erro_mp = response.text[:300]
            await query.message.reply_text(f"❌ Erro ao gerar o Pix:\n`{erro_mp}`", parse_mode="Markdown")

    elif data.startswith("check_"):
        payment_id = data.split("_")[1]
        
        url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            resp_data = response.json()
            status = resp_data.get("status")
            
            if status == "approved":
                await query.message.reply_text(
                    f"🎉 **Pagamento Aprovado com Sucesso!**\n\n"
                    f"Muito obrigado pela compra! Aqui está o seu link de acesso exclusivo:\n{LINK_DO_GRUPO}"
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
    
    print("SanizinhaBot atualizado e rodando com segurança...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
