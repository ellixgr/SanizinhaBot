import os
import uuid
import time
import asyncio
import requests
import threading
from flask import Flask
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    TypeHandler, 
    ContextTypes,
    ApplicationHandlerStop,
    ChatMemberHandler
)

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "SanizinhaBot está online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

TELEGRAM_TOKEN = "8919678511:AAEzQ7m2NA2vHeA9UYXo9HxztXtursMo3oI"
MP_ACCESS_TOKEN = "APP_USR-2233798366076054-072321-1ebc8660b5623826d8e956f1d629fa98-805811682"
DONO_ID = 7711945457
CANAL_ALVO_ID = -1007711945457  # Substitua pelo ID real do seu canal/grupo

# CONEXÃO COM O MONGODB ATLAS (Nuvem Segura)
MONGO_URI = "mongodb+srv://sanibronx21_db_user:<db_password>@cluster0.olwogxx.mongodb.net/?appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["sanizinhabot_db"]
collection_clientes = db["clientes"]

TEMPO_INICIAL = time.time()
FOTO_START = "https://files.catbox.moe/0pw3k8.jpg"

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
        if bloqueio_temporario[user_id] - agora > 0:
            raise ApplicationHandlerStop  
        else:
            del bloqueio_temporario[user_id]
            contador_spam.pop(user_id, None)
                
    if user_id in usuarios_bloqueados:
        raise ApplicationHandlerStop        

    if user_id in ultimo_envio:
        if agora - ultimo_envio[user_id] < 1.2:
            contador_spam[user_id] = contador_spam.get(user_id, 0) + 1
            ultimo_envio[user_id] = agora
            if contador_spam[user_id] >= 8:
                bloqueio_temporario[user_id] = agora + 300  
                contador_spam[user_id] = 0
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ **Muitas mensagens enviadas rapidamente. Aguarde alguns instantes.**",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
                raise ApplicationHandlerStop           
            raise ApplicationHandlerStop
            
    ultimo_envio[user_id] = agora

async def verificar_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if not result:
        return        
    chat = result.chat
    new_status = result.new_chat_member.status
    actor = result.from_user
    if chat.type in ["group", "supergroup", "channel"] and new_status in ["member", "administrator"]:
        if actor and actor.id != DONO_ID:
            try:
                await context.bot.leave_chat(chat.id)
            except Exception:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    texto_boas_vindas = (
        "🔥 **SEJA BEM-VINDO AO CANAL EXCLUSIVO** 🇧🇷\n\n"
        "✨ Tenha acesso completo a todo o nosso conteúdo diário atualizado em um só lugar:\n\n"
        "📁 +130 mil mídias disponíveis (vídeos e fotos)\n"
        "🚀 Atualizações diárias sem censura\n"
        "💎 Material organizado e exclusivo\n\n"
        "👇 Escolha o seu plano abaixo para liberar o seu acesso:\n\n"
        "💡 *Precisa de ajuda? Fale com o suporte:* @Lyhhxv"
    )
    keyboard = [
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐃𝐈𝐀 → R$ 2,00 🔥", callback_data="comprar_2.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐒𝐄𝐌𝐀𝐍𝐀 → R$ 7,00", callback_data="comprar_7.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐌𝐄𝐒 → R$ 20,00", callback_data="comprar_20.00")],
        [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐄𝐑𝐌𝐀ℕ𝐄ℕ𝐓𝐄 → R$ 60,00", callback_data="comprar_60.00")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_photo(
            photo=FOTO_START,
            caption=texto_boas_vindas,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text(texto_boas_vindas, reply_markup=reply_markup, parse_mode="Markdown")

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    resposta = (
        f"📊 **INFORMAÇÕES DE ID:**\n\n"
        f"💬 **Nome do Chat:** {chat.title if chat.title else 'Privado'}\n"
        f"🆔 **ID deste Chat/Grupo:** `{chat.id}`\n"
        f"👤 **Seu ID de Usuário:** `{user.id}`"
    )
    await update.message.reply_text(resposta, parse_mode="Markdown")

async def teste_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    msg_teste = (
        f"🧪 **DADOS CAPTURADOS (COMANDO /TESTE)!** 🧪\n\n"
        f"👤 **Nome:** {user.first_name or 'Sem nome'}\n"
        f"🔗 **Username:** @{user.username if user.username else 'Sem @username'}\n"
        f"🆔 **ID do Telegram:** `{user.id}`\n\n"
        f"✅ *O bot enviou esta mensagem diretamente para o seu privado com sucesso!*"
    )
    await update.message.reply_text("✅ Teste executado! Os dados foram enviados lá no seu privado.")
    try:
        await context.bot.send_message(chat_id=DONO_ID, text=msg_teste, parse_mode="Markdown")
    except Exception:
        pass

async def comandos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📜 **LISTA DE COMANDOS DO BOT** 📜\n\n"
        "👤 **Comandos Disponíveis:**\n"
        "• `/start` - Inicia o bot e exibe os planos\n"
        "• `/id` - Mostra o ID exato do grupo ou chat atual\n"
        "• `/teste` - Testa o envio de dados\n"
        "• `/suporte` - Mostra o contato do suporte\n"
        "• `/comandos` - Mostra esta lista de comandos\n"
        "• `/ping` - Mostra a latência e o status da hospedagem"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inicio = time.time()
    msg = await update.message.reply_text("pong 🏓...")
    latencia = int((time.time() - inicio) * 1000)
    uptime = int(time.time() - TEMPO_INICIAL)
    resposta = (
        f"🏓 **PONG! Informações do Sistema:**\n\n"
        f"⚡ **Latência:** `{latencia}ms`\n"
        f"⏳ **Uptime:** `{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s`\n"
        f"🧠 **Memória RAM:** `512 MB (Render Cloud Gratuito)`\n"
        f"💻 **CPU:** `Instância Compartilhada`"
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
                "first_name": user.first_name or "Cliente",
                "last_name": user.last_name or "Telegram"
            }
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
        except Exception:
            await query.message.reply_text("❌ Erro de conexão com o gateway de pagamento. Tente novamente.", parse_mode="Markdown")
            return
        if response.status_code == 201:
            resp_data = response.json()
            payment_id = resp_data["id"]
            qr_data = resp_data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
            msg_completa = (
                f"✅ **PIX Gerado com Sucesso!**\n\n"
                f"💰 **Valor:** R$ {valor:.2f}\n\n"
                f"📋 **Código Pix Copia e Cola:**\n`{qr_data}`"
            )
            
            keyboard_final = [
                [InlineKeyboardButton("📋 Copiar Código Pix", copy_text=dict(text=qr_data))],
                [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_{payment_id}")]
            ]
            
            await query.message.reply_text(
                msg_completa,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard_final)
            )
        else:
            await query.message.reply_text(f"❌ Erro ao gerar o Pix:\n`{response.text[:300]}`", parse_mode="Markdown")
            
    elif data.startswith("check_"):
        payment_id = data.split("_")[1]       
        url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}      
        try:
            response = requests.get(url, headers=headers, timeout=10)
        except Exception:
            await query.message.reply_text("❌ Erro de conexão ao verificar pagamento. Tente novamente.", parse_mode="Markdown")
            return
        if response.status_code == 200:
            resp_data = response.json()
            if resp_data.get("status") == "approved":
                try:
                    await query.answer("🎉 Pagamento Aprovado!", show_alert=True)
                except Exception:
                    pass              

                valor_pago = float(resp_data.get("transaction_amount", 0.0))
                
                # Calcular tempo de expiração
                duracao_segundos = 86400  # Padrão 1 dia (R$ 2,00)
                if valor_pago == 7.0:
                    duracao_segundos = 86400 * 7
                elif valor_pago == 20.0:
                    duracao_segundos = 86400 * 30
                elif valor_pago == 60.0:
                    duracao_segundos = 86400 * 365 * 10  # Permanente
                
                user_id = update.effective_user.id
                tempo_expiracao = time.time() + duracao_segundos
                
                # Salvar ou atualizar no MongoDB Atlas (nuvem)
                collection_clientes.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "user_id": user_id,
                            "nome": update.effective_user.first_name or "Cliente",
                            "expira_em": tempo_expiracao,
                            "aviso_1dia_enviado": False,
                            "aviso_20min_enviado": False
                        }
                    },
                    upsert=True
                )

                # Gerar link de convite único
                link_convite_gerado = None
                try:
                    chat_invite = await context.bot.create_chat_invite_link(
                        chat_id=CANAL_ALVO_ID,
                        member_limit=1,
                        expire_date=int(time.time()) + 86400
                    )
                    link_convite_gerado = chat_invite.invite_link
                except Exception:
                    link_convite_gerado = None

                texto_link = f"Aqui está o seu link de acesso exclusivo:\n{link_convite_gerado}" if link_convite_gerado else "⚠️ Entre em contato com o suporte (@Lyhhxv) para liberar seu acesso."

                await query.message.reply_text(
                    f"🎉 **Pagamento Aprovado com Sucesso!**\n\n"
                    f"Muito obrigado pela compra!\n{texto_link}"
                )

                if payment_id not in pagamentos_notificados:
                    pagamentos_notificados.add(payment_id)
                    plano_nome = "1 Dia 🔥 (R$ 2,00)" if valor_pago == 2.0 else "1 Semana (R$ 7,00)" if valor_pago == 7.0 else "1 Mês (R$ 20,00)" if valor_pago == 20.0 else "Permanente (R$ 60,00)" if valor_pago == 60.0 else f"Personalizado (R$ {valor_pago:.2f})"
                    comprador = update.effective_user
                    relatorio_privado = (
                        f"🚨 **NOVA ASSINATURA CONFIRMADA!** 🚨\n\n"
                        f"👤 **Cliente:** {comprador.first_name or 'Sem nome'}\n"
                        f"🔗 **Username:** @{comprador.username if comprador.username else 'Sem @'}\n"
                        f"🆔 **ID do Telegram:** `{comprador.id}`\n"
                        f"💰 **Valor Pago:** R$ {valor_pago:.2f}\n"
                        f"📅 **Plano Escolhido:** {plano_nome}\n"
                        f"⏰ **Data/Hora:** {time.strftime('%d/%m/%Y às %H:%M:%S', time.localtime())}\n"
                        f"🧾 **ID do Pix:** `{payment_id}`\n"
                        f"🟢 **Status:** Aprovado"
                    )
                    try:
                        await context.bot.send_message(chat_id=DONO_ID, text=relatorio_privado, parse_mode="Markdown")
                    except Exception:
                        pass
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

    elif data == "renovar_2.00":
        query.data = "comprar_2.00"
        await button_handler(update, context)

    elif data == "ver_outros_precos":
        keyboard = [
            [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐒𝐄𝐌𝐀𝐍𝐀 → R$ 7,00", callback_data="comprar_7.00")],
            [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐎𝐑 1 𝐌𝐄𝐒 → R$ 20,00", callback_data="comprar_20.00")],
            [InlineKeyboardButton("𝐀𝐂𝐄𝐒𝐒𝐎 𝐏𝐄𝐑𝐌𝐀ℕ𝐄ℕ𝐓𝐄 → R$ 60,00", callback_data="comprar_60.00")]
        ]
        await query.message.reply_text("Escolha outro plano abaixo:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- TAREFA EM SEGUNDO PLANO PARA CONTROLAR OS PRAZOS E AVISOS (MONGODB) ---
async def gerenciador_assinaturas(application):
    await asyncio.sleep(10)  # Espera o bot iniciar
    while True:
        try:
            agora = time.time()
            clientes = collection_clientes.find({})

            for cliente in clientes:
                user_id = cliente["user_id"]
                expira_em = cliente["expira_em"]
                tempo_restante = expira_em - agora

                # 1. Aviso faltando 1 dia (entre 23h e 24h restantes)
                if 82800 <= tempo_restante <= 86400 and not cliente.get("aviso_1dia_enviado", False):
                    try:
                        msg = (
                            "⚠️ **SEU PLANO VENCE AMANHÃ!** ⚠️\n\n"
                            "O seu acesso ao nosso canal exclusivo expira em breve. "
                            "Não fique de fora das atualizações diárias!\n\n"
                            "👇 Renove agora mesmo para continuar garantindo o seu acesso:"
                        )
                        keyboard = [
                            [InlineKeyboardButton("🔄 Continuar Assinado (R$ 2,00 - 1 Dia)", callback_data="renovar_2.00")],
                            [InlineKeyboardButton("💎 Ver Outros Planos", callback_data="ver_outros_precos")]
                        ]
                        await application.bot.send_message(chat_id=user_id, text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                        collection_clientes.update_one({"user_id": user_id}, {"$set": {"aviso_1dia_enviado": True}})
                    except Exception:
                        pass

                # 2. Aviso faltando 20 minutos (entre 0 e 1200 segundos restantes)
                elif 0 < tempo_restante <= 1200 and not cliente.get("aviso_20min_enviado", False):
                    try:
                        msg = (
                            "🚨 **ATENÇÃO: SEU PLANO EXPIRA EM POUCOS MINUTOS!** 🚨\n\n"
                            "O seu tempo está acabando e você será removido do canal em breve. "
                            "Garanta sua permanência agora para não perder nenhum conteúdo!\n\n"
                            "👇 Pague agora e continue com acesso liberado:"
                        )
                        keyboard = [
                            [InlineKeyboardButton("🔄 Continuar Assinado por R$ 2,00", callback_data="renovar_2.00")],
                            [InlineKeyboardButton("📋 Ver Outros Preços", callback_data="ver_outros_precos")]
                        ]
                        await application.bot.send_message(chat_id=user_id, text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                        collection_clientes.update_one({"user_id": user_id}, {"$set": {"aviso_20min_enviado": True}})
                    except Exception:
                        pass

                # 3. Tempo esgotado: Expulsar do canal e remover do banco
                elif tempo_restante <= 0:
                    try:
                        await application.bot.ban_chat_member(chat_id=CANAL_ALVO_ID, user_id=user_id)
                        await application.bot.unban_chat_member(chat_id=CANAL_ALVO_ID, user_id=user_id)
                        
                        await application.bot.send_message(
                            chat_id=user_id,
                            text="❌ **Seu plano expirou e você foi removido do canal.**\n\n"
                                 "Para entrar novamente, basta iniciar o bot com `/start` e adquirir um novo plano!",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
                    
                    # Deletar do banco de dados na nuvem
                    collection_clientes.delete_one({"user_id": user_id})

        except Exception as e:
            print(f"Erro no gerenciador: {e}")

        await asyncio.sleep(60)  # Roda a verificação a cada 1 minuto

def run_background_loop(application):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gerenciador_assinaturas(application))

def main():
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Iniciar thread de checagem de prazos com MongoDB
    threading.Thread(target=run_background_loop, args=(app,), daemon=True).start()

    app.add_handler(TypeHandler(Update, interceptador_universal), group=-1)
    app.add_handler(ChatMemberHandler(verificar_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("teste", teste_cmd))
    app.add_handler(CommandHandler("comandos", comandos_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler(["suport", "suporte"], suporte_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))    
    
    print("𝐓𝐎 𝐎𝐍 𝐁𝐁 😗")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
