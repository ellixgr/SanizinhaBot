import os
import uuid
import random
import time
import requests
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, TypeHandler, filters, ContextTypes

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "SanizinhaBot está online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# CONFIGURAÇÕES DO BOT, MERCADO PAGO E SEU ID DE ADMIN
TELEGRAM_TOKEN = "8634433708:AAGH67_iFaiMDHHPOVBQUx_GpxOlM-Lu97c"
MP_ACCESS_TOKEN = "APP_USR-4578357640781383-101515-089e854df4cde17d09a4e28316782210-2028678149"
LINK_DO_GRUPO = "https://t.me/+ZWUMQ-KbutpkY2Yx"

# SEU ID NUMÉRICO CONFIGURADO CORRETAMENTE
DONO_ID = 7106368383

# TEMPO DE INÍCIO DO BOT (PARA CALCULO DE UPTIME)
TEMPO_INICIAL = time.time()

# LISTA DE VÍDEOS PARA ENVIO ALEATÓRIO NO START
VIDEOS_START = [
    "https://ellixgr.github.io/x23wzp/VID_20260713_133754_437.mp4",
    "https://ellixgr.github.io/x23wzp/1783749549965.mp4",
    "https://ellixgr.github.io/x23wzp/1783749723785.mp4"
]

# CONTROLE DE ESTADOS DE SUPORTE E USUÁRIOS
flood_control = {}
usuarios_bloqueados = {}  
chat_ativo = {"user_id": None, "timer": None}

async def global_block_and_flood_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepta ABSOLUTAMENTE TUDO (comandos, fotos, vídeos, textos). Se flodou, bloqueia e para."""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id

    if user_id == DONO_ID:
        return

    # Se já está bloqueado, barra a execução completamente
    if user_id in usuarios_bloqueados:
        raise ApplicationHandlerStop

    agora = time.time()
    if user_id not in flood_control:
        flood_control[user_id] = []
    
    # Limpa registros antigos (> 5 segundos)
    flood_control[user_id] = [t for t in flood_control[user_id] if agora - t < 5]
    flood_control[user_id].append(agora)

    # Se mandou mais de 4 mensagens/comandos/mídias em 5 segundos, bloqueia de vez
    if len(flood_control[user_id]) > 4:
        nome = user.first_name if user.first_name else "Desconhecido"
        username = user.username if user.username else "Sem username"
        usuarios_bloqueados[user_id] = {
            "nome": nome,
            "username": username,
            "motivo": "Flood excessivo de mensagens, mídias ou comandos"
        }
        raise ApplicationHandlerStop

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
        "🔥 𝐍𝐨𝐯𝐢𝐧𝐡𝐚𝐬⁺¹⁸ 𝐩𝐨𝐛𝐫𝐞 𝐪𝐮𝐞 𝐧𝐚𝐨 𝐭𝐞𝐦 𝐟𝐫𝐞𝐬𝐜𝐮𝐫𝐚\n\n"
        "👇 Escolha o seu plano abaixo:\n\n"
        "💡 *Precisa de ajuda? Fale com o suporte:* @Lyhhxv"
    )

    keyboard = [
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

async def comandos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = (
        "📜 **LISTA DE COMANDOS DO BOT** 📜\n\n"
        "👤 **Comandos para Membros:**\n"
        "• `/start` - Inicia o bot e exibe os planos\n"
        "• `/suport` ou `/suporte` - Mostra o contato do suporte\n"
        "• `/comandos` - Mostra esta lista de comandos\n"
        "• `/ping` - Mostra a latência e o status da hospedagem\n\n"
    )

    if user_id == DONO_ID:
        texto += (
            "🛠 **Comandos Exclusivos do Dono:**\n"
            "• `/falar [ID] [mensagem]` - Responde a um usuário específico\n"
            "• `/bloqueados` - Lista os usuários bloqueados/ignorados\n"
            "• `/desbloquear [ID, @username ou número]` - Remove o bloqueio de um usuário\n"
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

    if latencia < 300:
        status_icone = "🟢"
        status_texto = "Excelente (Normal)"
    elif latencia < 800:
        status_icone = "🟡"
        status_texto = "Moderado / Instável"
    else:
        status_icone = "🔴"
        status_texto = "Atenção / Alta Latência"

    resposta = (
        f"🏓 **PONG! Informações do Sistema:**\n\n"
        f"⚡ **Latência:** `{latencia}ms`\n"
        f"⏳ **Uptime:** `{uptime_str}`\n"
        f"🧠 **Memória RAM:** `512 MB (Render Cloud Gratuito)`\n"
        f"💻 **CPU:** `Instância Compartilhada`\n"
        f"📊 **Status:** {status_icone} {status_texto}"
    )

    await msg.edit_text(resposta, parse_mode="Markdown")

async def suporte_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 **Central de Suporte**\n\n"
        "Para tirar dúvidas ou resolver qualquer problema, entre em contato diretamente com o nosso suporte:\n\n"
        "👉 **@Lyhhxv**",
        parse_mode="Markdown"
    )

async def fechar_suporte_por_timeout(context: ContextTypes.DEFAULT_TYPE):
    if chat_ativo["user_id"] is not None:
        user_id = chat_ativo["user_id"]
        chat_ativo["user_id"] = None
        chat_ativo["timer"] = None
        try:
            await context.bot.send_message(
                chat_id=DONO_ID,
                text="⏱ **Modo suporte encerrado automaticamente por inatividade (1 minuto sem resposta).**"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="🔒 O atendimento de suporte foi encerrado por inatividade."
            )
        except Exception as e:
            print(f"Erro no timeout de suporte: {e}")

async def falar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return  

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ **Uso incorreto!**\n"
            "Formato correto: `/falar ID_DO_USUARIO sua mensagem aqui`",
            parse_mode="Markdown"
        )
        return

    target_user_id = int(args[0])
    mensagem_resposta = " ".join(args[1:])

    chat_ativo["user_id"] = target_user_id

    if chat_ativo["timer"]:
        chat_ativo["timer"].cancel()

    timer = threading.Timer(60.0, lambda: context.application.create_task(fechar_suporte_por_timeout(context)))
    timer.start()
    chat_ativo["timer"] = timer

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🛠 **Mensagem da Administração / Suporte:**\n\n{mensagem_resposta}"
        )
        await update.message.reply_text(f"✅ Mensagem enviada para o usuário `{target_user_id}`!\n⏱ *Cronômetro de 1 minuto iniciado.*", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao enviar mensagem para o usuário:\n`{e}`", parse_mode="Markdown")

async def bloqueados_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return

    if not usuarios_bloqueados:
        await update.message.reply_text("📂 Não há usuários ignorados pelo bot no momento.")
        return

    texto = "🚫 **Lista de Usuários Ignorados (Bloqueados):**\n\n"
    for uid, dados in usuarios_bloqueados.items():
        texto += (
            f"🆔 **ID:** `{uid}`\n"
            f"👤 **Nome:** {dados['nome']}\n"
            f"🔗 **Username:** @{dados['username']}\n"
            f"📌 **Motivo:** {dados['motivo']}\n"
            f"-----------------------------------\n"
        )
    
    await update.message.reply_text(texto, parse_mode="Markdown")

async def desbloquear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ **Uso incorreto!**\n"
            "Informe o ID, @username ou número do usuário.\n"
            "Exemplo: `/desbloquear 123456789` ou `/desbloquear @username`",
            parse_mode="Markdown"
        )
        return

    alvo = args[0].strip().replace("@", "")
    removido = False

    for uid in list(usuarios_bloqueados.keys()):
        dados = usuarios_bloqueados[uid]
        if str(uid) == alvo or dados['username'].lower() == alvo.lower() or str(uid).endswith(alvo):
            del usuarios_bloqueados[uid]
            removido = True
            await update.message.reply_text(f"✅ O bot parou de ignorar o usuário `{uid}` (`@{dados['username']}`) e voltou a responder!", parse_mode="Markdown")
            break

    if not removido:
        await update.message.reply_text("❌ Nenhum usuário encontrado com esse ID, username ou número na lista de ignorados.")

async def encaminhar_para_dono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == DONO_ID:
        return

    texto_usuario = update.effective_message.text
    if texto_usuario and texto_usuario.strip().lower() in ["oi", "oii", "oiii", "ola", "olá"]:
        keyboard = [
            [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐒𝐄𝐌𝐀𝐍𝐀 → R$ 7,00", callback_data="comprar_7.00")],
            [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐌𝐄𝐒 → R$ 20,00", callback_data="comprar_20.00")],
            [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐄𝐑𝐌𝐀ℕ𝐄ℕ𝐓𝐄 → R$ 60,00", callback_data="comprar_60.00")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Oi, tudo bem? Vai assinar os seus conteúdos? 😏\n\nEscolha o seu plano abaixo:",
            reply_markup=reply_markup
        )
        return

    if chat_ativo["user_id"] == user.id:
        if chat_ativo["timer"]:
            chat_ativo["timer"].cancel()
        timer = threading.Timer(60.0, lambda: context.application.create_task(fechar_suporte_por_timeout(context)))
        timer.start()
        chat_ativo["timer"] = timer

    if update.effective_chat.type == "private" and DONO_ID != 0:
        try:
            await context.bot.forward_message(
                chat_id=DONO_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id
            )
            
            nome_temp = user.first_name if user.first_name else "Desconhecido"
            username_temp = user.username if user.username else "Sem username"
            
            keyboard_dono = [
                [
                    InlineKeyboardButton("🚫 Ignorar Usuário", callback_data=f"bloquear_{user.id}"),
                    InlineKeyboardButton("💬 Responder", callback_data=f"resp_{user.id}")
                ]
            ]
            
            await context.bot.send_message(
                chat_id=DONO_ID,
                text=f"⬆️ *Mensagem recebida de:* {nome_temp} (`@{username_temp}` | ID: `{user.id}`)",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard_dono)
            )
        except Exception as e:
            print(f"Erro ao encaminhar mensagem: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id_atual = update.effective_user.id

    if user_id_atual != DONO_ID and user_id_atual in usuarios_bloqueados:
        return

    if data.startswith("bloquear_"):
        if user_id_atual != DONO_ID:
            await query.answer("❌ Apenas o dono pode usar isso!", show_alert=True)
            return
        
        target_id = int(data.split("_")[1])
        try:
            chat_member = await context.bot.get_chat(target_id)
            nome = chat_member.first_name or "Desconhecido"
            username = chat_member.username or "Sem username"
        except Exception:
            nome = "Desconhecido"
            username = "Sem username"

        usuarios_bloqueados[target_id] = {
            "nome": nome,
            "username": username,
            "motivo": "Bloqueado via botão de atalho"
        }
        await query.answer(f"🚫 Usuário {target_id} adicionado à lista de ignorados!", show_alert=True)
        await query.edit_message_text(f"🚫 **Usuário `{target_id}` foi bloqueado/ignorado com sucesso.**", parse_mode="Markdown")
        return

    if data.startswith("resp_"):
        if user_id_atual != DONO_ID:
            await query.answer("❌ Apenas o dono pode usar isso!", show_alert=True)
            return
        
        target_id = int(data.split("_")[1])
        await query.answer()
        await query.message.reply_text(
            f"✏️ Para responder este usuário, digite:\n`/falar {target_id} sua mensagem aqui`",
            parse_mode="Markdown"
        )
        return

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
    
    # TYPEHANDLER GLOBAL: Intercepta QUALQUER coisa que venha do Telegram antes de comandos ou mensagens
    app.add_handler(TypeHandler(Update, global_block_and_flood_filter), group=-1)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler(["suport", "suporte"], suporte_cmd))
    app.add_handler(CommandHandler("falar", falar_cmd))
    app.add_handler(CommandHandler("bloqueados", bloqueados_cmd))
    app.add_handler(CommandHandler("desbloquear", desbloquear_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, encaminhar_para_dono))
    
    print("SanizinhaBot totalmente otimizado e rodando...")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
