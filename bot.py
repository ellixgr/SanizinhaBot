import os
import uuid
import random
import time
import requests
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    TypeHandler, 
    filters, 
    ContextTypes,
    ApplicationHandlerStop
)

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "SanizinhaBot está online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# CONFIGURAÇÕES DO BOT E DO MERCADO PAGO
TELEGRAM_TOKEN = "8634433708:AAGH67_iFaiMDHHPOVBQUx_GpxOlM-Lu97c"
MP_ACCESS_TOKEN = "APP_USR-4578357640781383-101515-089e854df4cde17d09a4e28316782210-2028678149"

# LINK DO SEU GRUPO VIP DE CLIENTES
LINK_DO_GRUPO = "https://t.me/+LCsNZuCgCWxiYzNh"

# ID NUMÉRICO DO SEU GRUPO ONDE O BOT VAI ENVIAR OS DADOS (Ex: -100xxxxxxxxxx)
GRUPO_ALVO_ID = -1001234567890  # <-- MUDE ESTE NÚMERO PARA O ID REAL DO SEU GRUPO CLIENTES

# TEMPO DE INÍCIO DO BOT (PARA CALCULO DE UPTIME)
TEMPO_INICIAL = time.time()

# LISTA DE VÍDEOS PARA ENVIO ALEATÓRIO NO START
VIDEOS_START = [
    "https://ellixgr.github.io/x23wzp/VID_20260713_133754_437.mp4",
    "https://ellixgr.github.io/x23wzp/1783749549965.mp4",
    "https://ellixgr.github.io/x23wzp/1783749723785.mp4"
]

# CONTROLE DE ESTADOS E SPAM
ultimo_envio = {}          
contador_spam = {}         
usuarios_bloqueados = {}     
bloqueio_temporario = {}     
pagamentos_notificados = set() 

async def interceptador_universal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    agora = time.time()

    if user_id in bloqueio_temporario:
        tempo_restante = bloqueio_temporario[user_id] - agora
        if tempo_restante > 0:
            raise ApplicationHandlerStop  
        else:
            del bloqueio_temporario[user_id]
            if user_id in contador_spam:
                del contador_spam[user_id]

    if user_id in usuarios_bloqueados:
        raise ApplicationHandlerStop

    if user_id in ultimo_envio:
        diferenca = agora - ultimo_envio[user_id]
        if diferenca < 5.0:
            contador_spam[user_id] = contador_spam.get(user_id, 0) + 1
            ultimo_envio[user_id] = agora

            if contador_spam[user_id] >= 6:
                bloqueio_temporario[user_id] = agora + 600  
                contador_spam[user_id] = 0
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ **Você está bloqueado temporariamente por 10 minutos devido ao envio excessivo de comandos ou mensagens seguidas.**",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
                raise ApplicationHandlerStop
            
            raise ApplicationHandlerStop

    ultimo_envio[user_id] = agora

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_boas_vindas = (
        "🔥 𝗦𝗘𝗝𝗔 𝗕𝗘𝗠-𝗩𝗜𝗡𝗗𝗢 𝗔𝗢 𝗨𝗡𝗜𝗩𝗘𝗥𝗦𝗢 𝗗𝗔𝗦 𝗙𝗔𝗩𝗘𝗟𝗔𝗗𝗜𝗡𝗛𝗔𝗦 𝗚𝗢𝗦𝗧𝗢𝗦𝗔𝗦 🇧🇷\n\n"
        "🇧🇷 𝙁𝙖𝙫𝙚𝙡𝙖𝙙𝙞𝙣𝙝𝙖𝙨, 𝙙𝙚𝙨𝙚𝙨𝙥𝙚𝙧𝙖𝙙𝙖𝙨, 𝙣𝙞𝙣𝙛𝙚𝙩𝙖𝙨 𝙙𝙖 𝙘𝙖𝙨𝙖 𝙨em 𝙧𝙚𝙗𝙤𝙘𝙤, 𝙢𝙖𝙜𝙧𝙞𝙣𝙝𝙖𝙨 𝙥𝙚𝙞𝙩𝙪𝙙𝙖𝙨, 𝙩𝙪𝙙𝙤 𝙚𝙢 1 𝙂𝙍𝙐𝙋O 😈\n\n"
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
        "🔥 𝐍𝐨𝐯𝐢𝐧𝐡𝐚𝐬⁺¹⁸ 𝐩𝐨𝐛𝐫𝐞 𝙦𝙪𝙚 𝙣𝙖𝙤 𝙩𝙚𝙢 𝙛𝙧𝙚𝙨𝙘𝙪𝙧𝙖\n\n"
        "👇 Escolha o seu plano abaixo:\n\n"
        "💡 *Precisa de ajuda? Fale com o suporte:* @Lyhhxv"
    )

    keyboard = [
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐃𝐈𝐀 → R$ 2,00 🔥", callback_data="comprar_2.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐒𝐄𝐌𝐀𝐍𝐀 → R$ 7,00", callback_data="comprar_7.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐌𝐄𝐒 → R$ 20,00", callback_data="comprar_20.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐄𝐑𝐌𝐀ℕ𝐄ℕ𝐓𝐄 → R$ 60,00", callback_data="comprar_60.00")]
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

async def teste_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    nome = user.first_name if user.first_name else "Sem nome"
    username = f"@{user.username}" if user.username else "Sem @username"
    user_id = user.id

    msg_teste = (
        f"🧪 **DADOS CAPTURADOS (COMANDO /TESTE)!** 🧪\n\n"
        f"👤 **Nome:** {nome}\n"
        f"🔗 **Username:** {username}\n"
        f"🆔 **ID do Telegram:** `{user_id}`\n\n"
        f"✅ *O bot enviou esta mensagem diretamente para o grupo com sucesso!*"
    )

    await update.message.reply_text("✅ Teste executado! Os dados foram enviados lá no grupo.")

    try:
        await context.bot.send_message(
            chat_id=GRUPO_ALVO_ID,
            text=msg_teste,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Erro ao enviar teste para o grupo: {e}")

async def comandos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📜 **LISTA DE COMANDOS DO BOT** 📜\n\n"
        "👤 **Comandos Disponíveis:**\n"
        "• `/start` - Inicia o bot e exibe os planos\n"
        "• `/teste eu` - Testa o envio de dados direto para o grupo\n"
        "• `/suport` ou `/suporte` - Mostra o contato do suporte\n"
        "• `/comandos` - Mostra esta lista de comandos\n"
        "• `/ping` - Mostra a latência e o status da hospedagem\n"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inicio = time.time()
    msg = await update.message.reply_text("pong 🏓...")
    fim = time.time()
    latencia = int((fim - inicio) * 1000)

    uptime_segundos = int(time.time() - TEMPO_INICIAL)
    horas = uptime_segundos // 3600
    minutos = (uptime_segundos % 3600) // 60
    segundos = uptime_segundos % 60
    uptime_str = f"{horas}h {minutos}m {segundos}s"

    resposta = (
        f"🏓 **PONG! Informações do Sistema:**\n\n"
        f"⚡ **Latência:** `{latencia}ms`\n"
        f"⏳ **Uptime:** `{uptime_str}`\n"
        f"🧠 **Memória RAM:** `512 MB (Render Cloud Gratuito)`\n"
        f"💻 **CPU:** `Instância Compartilhada`\n"
    )
    await msg.edit_text(resposta, parse_mode="Markdown")

async def suporte_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 **Central de Suporte**\n\n"
        "Para tirar dúvidas ou resolver qualquer problema, entre em contato diretamente com o nosso suporte:\n\n"
        "👉 **@Lyhhxv**",
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
                "📋 **Código Pix Copia e Cola:**\n"
                f"`{qr_data}`\n\n"
                "💡 *Basta tocar em cima do código acima para copiar automaticamente.*"
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

                if payment_id not in pagamentos_notificados:
                    pagamentos_notificados.add(payment_id)

                    valor_pago = float(resp_data.get("transaction_amount", 0.0))
                    
                    if valor_pago == 2.0:
                        plano_nome = "1 Dia 🔥"
                    elif valor_pago == 7.0:
                        plano_nome = "1 Semana"
                    elif valor_pago == 20.0:
                        plano_nome = "1 Mês"
                    elif valor_pago == 60.0:
                        plano_nome = "Permanente"
                    else:
                        plano_nome = f"R$ {valor_pago:.2f}"

                    comprador = update.effective_user
                    nome_cliente = comprador.first_name if comprador.first_name else "Sem nome"
                    username_cliente = f"@{comprador.username}" if comprador.username else "Sem @username"
                    id_cliente = comprador.id

                    relatorio_grupo = (
                        f"🚨 **NOVA ASSINATURA CONFIRMADA!** 🚨\n\n"
                        f"👤 **Cliente:** {nome_cliente}\n"
                        f"🔗 **Username:** {username_cliente}\n"
                        f"🆔 **ID do Telegram:** `{id_cliente}`\n"
                        f"💰 **Valor Pago:** R$ {valor_pago:.2f}\n"
                        f"📅 **Plano Escolhido:** {plano_nome}\n"
                        f"🧾 **ID do Pix:** `{payment_id}`"
                    )

                    try:
                        await context.bot.send_message(
                            chat_id=GRUPO_ALVO_ID,
                            text=relatorio_grupo,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"Erro ao enviar comprovante pro grupo: {e}")

            else:
                try:
                    await query.answer("❌ Pagamento ainda não identificado!", show_alert=True)
                except Exception:
                    pass
                await query.message.reply_text(
                    "⏳ **Pagamento ainda não identificado!**\n\n"
                    "Realize o pagamento no app do seu banco via Pix Copia e Cola. "
                    "Se você já pagou, aguarde alguns segundos e clique no botão novamente.",
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
    
    app.add_handler(TypeHandler(Update, interceptador_universal), group=-1)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("teste", teste_cmd))
    app.add_handler(CommandHandler("comandos", comandos_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler(["suport", "suporte"], suporte_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot rodando e configurado para enviar tudo direto no grupo!")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
