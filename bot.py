import os
import uuid
import random
import time
import requests
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "SanizinhaBot está online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# CONFIGURAÇÕES DO BOT, MERCADO PAGO E DONO
TELEGRAM_TOKEN = "8634433708:AAGH67_iFaiMDHHPOVBQUx_GpxOlM-Lu97c"
MP_ACCESS_TOKEN = "APP_USR-4578357640781383-101515-089e854df4cde17d09a4e28316782210-2028678149"
LINK_DO_GRUPO = "https://t.me/+ZWUMQ-KbutpkY2Yx"

# ⚠️ COLOQUE SEU ID NUMÉRICO DO TELEGRAM AQUI ABAIXO (Ex: 123456789)
DONO_ID = 0  # <--- SUBSTITUA O 0 PELO SEU ID REAL

# LISTA DE VÍDEOS PARA ENVIO ALEATÓRIO NO START
VIDEOS_START = [
    "https://ellixgr.github.io/x23wzp/VID_20260713_133754_437.mp4",
    "https://ellixgr.github.io/x23wzp/1783749549965.mp4",
    "https://ellixgr.github.io/x23wzp/1783749723785.mp4"
]

# CONTROLE DE ANTI-FLOOD E SESSÕES
user_cooldowns = {}
user_bans = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    agora = time.time()

    if user_id in user_bans:
        tempo_restante = user_bans[user_id] - agora
        if tempo_restante > 0:
            return 
        else:
            del user_bans[user_id]

    if user_id in user_cooldowns and (agora - user_cooldowns[user_id]) < 5:
        user_bans[user_id] = agora + 300 
        return
    user_cooldowns[user_id] = agora

    texto_boas_vindas = (
        "🔥 𝗦𝗘𝗝𝗔 𝗕𝗘𝗠-𝗩𝗜𝗡𝗗𝗢 𝗔𝗢 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗢 𝗗𝗔𝗦 𝗙𝗔𝗩𝗘𝗟𝗔𝗗𝗜𝗡𝗛𝗔𝗦 𝗚𝗢𝗦𝗧𝗢𝗦𝗔𝗦 🇧🇷\n\n"
        "🇧🇷 𝙁𝙖𝙫𝙚𝙡𝙖𝙙𝙞𝙣𝙝𝙖𝙨, 𝙙𝙚𝙨𝙚𝙨𝙥𝙚𝙧𝙖𝙙𝙖𝙨, 𝙣𝙞𝙣𝙛𝙚𝙩𝙖𝙨 𝙙𝙖 𝙘𝙖𝙨𝙖 𝙨em 𝙧𝙚𝙗𝙤𝙘𝙤, 𝙢𝙖𝙜𝙧𝙞𝙣𝙝𝙖𝙨 𝙥𝙚𝙞𝙩𝙪𝙙𝙖𝙨, 𝙩𝙪𝙙𝙤 𝙚𝙢 1 𝙂𝙍𝙐𝙋𝙊 😈\n\n"
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
        "👇 Escolha o seu plano abaixo:\n\n"
        "💡 *Precisa de ajuda? Use o comando:* `/suport [sua mensagem]`"
    )

    keyboard = [
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐒𝐄𝐌𝐀𝐍𝐀 → R$ 7,00", callback_data="comprar_7.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐌𝐄𝐒 → R$ 20,00", callback_data="comprar_20.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐄𝐑𝐌𝐀𝗡𝗘𝗡𝗧𝗘 → R$ 60,00", callback_data="comprar_60.00")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    video_escolhido = random.choice(VIDEOS_START)

    try:
        await update.message.reply_video(
            video=video_escolhido,
            caption=texto_boas_vindas,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text(texto_boas_vindas, reply_markup=reply_markup, parse_mode="Markdown")

# COMANDO DE SUPORTE PARA O CLIENTE
async def suporte_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text(
            "⚠️ **Uso incorreto do comando!**\n\n"
            "Por favor, escreva o motivo após o comando.\n"
            "Exemplo: `/suport paguei e o bot não me deu o link`",
            parse_mode="Markdown"
        )
        return

    motivo = " ".join(args)

    # Informa o usuário que o chamado foi aberto
    await update.message.reply_text(
        "✅ **Mensagem enviada para o suporte com sucesso!**\n\n"
        "O dono do bot recebeu seu chamado e responderá em breve por aqui.",
        parse_mode="Markdown"
    )

    # Se o ID do dono estiver configurado, envia a notificação para ele
    if DONO_ID != 0:
        msg_para_dono = (
            "🚨 **NOVO CHAMADO DE SUPORTE** 🚨\n\n"
            f"👤 **Nome:** {user.first_name} {user.last_name or ''}\n"
            f"🔗 **Username:** @{user.username if user.username else 'Sem username'}\n"
            f"🆔 **ID do Usuário:** `{user.id}`\n\n"
            f"💬 **Mensagem:** {motivo}\n\n"
            f"👉 *Para responder use:* `/falar {user.id} sua_resposta`"
        )
        try:
            await context.bot.send_message(chat_id=DONO_ID, text=msg_para_dono, parse_mode="Markdown")
        except Exception as e:
            print(f"Erro ao enviar aviso de suporte para o dono: {e}")

# COMANDO PARA O DONO FALAR COM O USUÁRIO
async def falar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return  # Ignora se não for o dono

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ **Uso incorreto!**\n"
            "Formato correto: `/falar ID_DO_USUARIO sua mensagem aqui`",
            parse_mode="Markdown"
        )
        return

    target_user_id = args[0]
    mensagem_resposta = " ".join(args[1:])

    try:
        await context.bot.send_message(
            chat_id=int(target_user_id),
            text=f"🛠 **Mensagem da Administração / Suporte:**\n\n{mensagem_resposta}"
        )
        await update.message.reply_text("✅ Mensagem enviada com sucesso para o usuário!")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao enviar mensagem para o usuário:\n`{e}`", parse_mode="Markdown")

# GERENCIADOR DE MENSAGENS NO PRIVADO (Repassa arquivos, fotos e textos do usuário para o Dono)
async def encaminhar_para_dono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Se quem mandou a mensagem for o dono no chat privado e ele não estiver respondendo via /falar, ignora
    if user.id == DONO_ID:
        return

    # Se for mensagem de chat privado de um cliente comum, encaminha para o Dono
    if update.effective_chat.type == "private" and DONO_ID != 0:
        await context.bot.forward_message(
            chat_id=DONO_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
        # Envia um lembrete prático do ID do usuário junto com o encaminhamento
        await context.bot.send_message(
            chat_id=DONO_ID,
            text=f"⬆️ *Mensagem recebida do usuário ID:* `{user.id}` ({user.first_name})\nPara responder: `/falar {user.id} sua_mensagem`",
            parse_mode="Markdown"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("comprar_"):
        try:
            await query.answer()
        except Exception:
            pass

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
                try:
                    await query.answer("🎉 Pagamento Aprovado!", show_alert=True)
                except Exception:
                    pass
                await query.message.reply_text(
                    f"🎉 **Pagamento Aprovado com Sucesso!**\n\n"
                    f"Muito obrigado pela compra! Aqui está o seu link de acesso exclusivo:\n{LINK_DO_GRUPO}"
                )
            else:
                try:
                    await query.answer("❌ Pagamento ainda não identificado!", show_alert=True)
                except Exception:
                    pass
                await query.message.reply_text(
                    "⏳ **Pagamento ainda não identificado!**\n\n"
                    "Realize o pagamento no app do seu banco via Pix Copia e Cola. "
                    "Se você já pagou, aguarde de 5 a 10 segundos para o banco processar e clique no botão novamente.",
                    parse_mode="Markdown"
                )
        else:
            try:
                await query.answer("❌ Erro ao consultar o Mercado Pago.", show_alert=True)
            except Exception:
                pass
            await query.message.reply_text("❌ Não foi possível verificar o pagamento no momento. Tente novamente em instantes.")

def main():
    t = threading.Thread(target=run_web)
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Handlers de comandos e botões
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["suport", "suporte"], suporte_cmd))
    app.add_handler(CommandHandler("falar", falar_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Handler para capturar qualquer mensagem enviada pelos usuários no privado (fotos, arquivos, textos)
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL & ~filters.COMMAND, encaminhar_para_dono))
    
    print("SanizinhaBot atualizado com sistema de suporte e rodando...")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
