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

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
DONO_ID = int(os.environ.get("DONO_ID", 7711945457))
CANAL_ALVO_ID = int(os.environ.get("CANAL_ALVO_ID"))

MONGO_URI = os.environ.get("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["sanizinhabot_db"]
collection_clientes = db["clientes"]
collection_chats = db["chats_autorizados"]

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
    
    # Se for o dono, libera a execução de tudo imediatamente
    if user_id == DONO_ID:
        return

    # Bloqueia comandos restritos para quem não é o dono
    if update.message and update.message.text and update.message.text.startswith('/'):
        cmd = update.message.text.split()[0].split('@')[0].lower()
        if cmd not in ['/start', '/suporte', '/suport']:
            raise ApplicationHandlerStop

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
    
    if chat.type in ["group", "supergroup", "channel"]:
        if new_status in ["member", "administrator"]:
            collection_chats.update_one(
                {"chat_id": chat.id},
                {"$set": {"chat_id": chat.id, "title": chat.title, "type": chat.type}},
                upsert=True
            )
        elif new_status in ["left", "kicked"]:
            collection_chats.delete_one({"chat_id": chat.id})

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
    if update.effective_user.id != DONO_ID:
        return
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
    if not user or user.id != DONO_ID:
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
    if update.effective_user.id != DONO_ID:
        return
    texto = (
        "📜 **LISTA DE COMANDOS DO BOT** 📜\n\n"
        "👤 **Comandos Disponíveis:**\n"
        "• `/start` - Inicia o bot e exibe os planos\n"
        "• `/id` - Mostra o ID exato do grupo ou chat atual\n"
        "• `/teste` - Testa o envio de dados\n"
        "• `/suporte` - Mostra o contato do suporte\n"
        "• `/comandos` - Mostra esta lista de comandos\n"
        "• `/ping` - Mostra a latência e o status da hospedagem\n"
        "• `/addusuario` - Adiciona um usuário manualmente a um plano\n"
        "• `/clientes` - Exibe todos os clientes ativos no grupo e suas informações\n"
        "• `/config` - Gerencia grupos e canais conectados ao bot\n"
        "• `/menu` - Mostra o painel completo com todos os comandos do bot"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    texto_menu = (
        "🎛 **PAINEL DE CONTROLE - MENU DO DONO** 🎛\n\n"
        "Aqui estão absolutamente **TODOS** os comandos integrados e operacionais do bot:\n\n"
        "🟢 **Comandos de Usuários/Públicos:**\n"
        "• `/start` - Inicia o bot, exibe a imagem e os planos de assinatura Pix.\n"
        "• `/suporte` (ou `/suport`) - Mostra o contato direto da central de atendimento.\n\n"
        "👑 **Comandos Exclusivos do Dono:**\n"
        "• `/menu` - Abre este painel completo com todos os comandos.\n"
        "• `/comandos` - Lista todos os comandos do sistema.\n"
        "• `/config` - Abre o painel interativo de grupos e canais para capturar IDs.\n"
        "• `/clientes` - Exibe a listagem completa de todos os clientes ativos no banco de dados com seus detalhes de expiração.\n"
        "• `/addusuario <id> plano <dias>` - Adiciona ou renova manualmente o acesso de um usuário.\n"
        "• `/id` - Mostra o ID do chat atual e do usuário.\n"
        "• `/teste` - Testa a captura de dados e envio para o privado do dono.\n"
        "• `/ping` - Verifica a latência da API, uptime do servidor e consumo de recursos.\n\n"
        "⚙️ **Sistemas Automáticos em Execução:**\n"
        "• Interceptador universal de anti-spam e bloqueio de comandos restritos.\n"
        "• Gerenciador automático de assinaturas (aviso de 1 dia, aviso de 20 minutos e banimento/remoção automática ao expirar).\n"
        "• Verificador automático de pagamento via API do Mercado Pago."
    )
    await update.message.reply_text(texto_menu, parse_mode="Markdown")

async def config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    
    chats = list(collection_chats.find({}))
    if not chats:
        await update.message.reply_text(
            "⚙️ **Painel de Configuração de Grupos/Canais**\n\n"
            "Nenhum grupo ou canal foi catalogado ainda.\n"
            "Adicione o bot como administrador em algum canal ou grupo para que ele apareça aqui automaticamente!",
            parse_mode="Markdown"
        )
        return

    keyboard = []
    for chat in chats:
        chat_id = chat["chat_id"]
        title = chat["title"] or f"Chat {chat_id}"
        tipo = chat.get("type", "grupo")
        emoji = "📢" if tipo == "channel" else "👥"
        keyboard.append([InlineKeyboardButton(f"{emoji} {title}", callback_data=f"cfg_chat_{chat_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ **Painel de Configuração de Grupos/Canais**\n\n"
        "Selecione abaixo o canal ou grupo que deseja gerenciar:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def clientes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    
    agora = time.time()
    clientes_cursor = collection_clientes.find({})
    lista_clientes = list(clientes_cursor)
    
    if not lista_clientes:
        await update.message.reply_text("📁 **Nenhum cliente ativo encontrado no banco de dados.**", parse_mode="Markdown")
        return
        
    resposta = f"📋 **LISTA DE CLIENTES ATIVOS ({len(lista_clientes)})**:\n\n"
    
    for i, cliente in enumerate(lista_clientes, 1):
        user_id = cliente.get("user_id")
        nome = cliente.get("nome", "Desconhecido")
        expira_em = cliente.get("expira_em", 0)
        
        tempo_restante = expira_em - agora
        if tempo_restante > 0:
            dias_Restantes = int(tempo_restante // 86400)
            horas_restantes = int((tempo_restante % 86400) // 3600)
            minutos_restantes = int((tempo_restante % 3600) // 60)
            if dias_Restantes > 365:
                tempo_str = "Permanente ♾️"
            else:
                tempo_str = f"{dias_Restantes}d {horas_restantes}h {minutos_restantes}m"
        else:
            tempo_str = "Expirado ❌"
            
        data_exp_formatada = time.strftime('%d/%m/%Y às %H:%M', time.localtime(expira_em)) if expira_em > 0 else "N/A"
        
        resposta += (
            f"🔹 **{i}. {nome}**\n"
            f"🆔 ID: `{user_id}`\n"
            f"⏳ Expira em: `{tempo_str}`\n"
            f"📅 Data limite: `{data_exp_formatada}`\n\n"
        )
        
        if len(resposta) > 3800:
            await update.message.reply_text(resposta, parse_mode="Markdown")
            resposta = ""
            
    if resposta:
        await update.message.reply_text(resposta, parse_mode="Markdown")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
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

async def addusuario_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Use: `/addusuario <id_usuario> plano <2|7|20|60>`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(args[0])
        plano_arg = args[1].lower()
        
        if plano_arg.startswith("plano"):
            if len(args) < 3:
                await update.message.reply_text("⚠️ Informe o valor do plano após a palavra 'plano'. Ex: `/addusuario 837382929 plano 2`", parse_mode="Markdown")
                return
            dias_valor = int(args[2])
        else:
            dias_valor = int(plano_arg)
            
        duracao_segundos = 86400  
        if dias_valor == 7:
            duracao_segundos = 86400 * 7
        elif dias_valor == 20:
            duracao_segundos = 86400 * 30
        elif dias_valor == 60:
            duracao_segundos = 86400 * 365 * 10  
        elif dias_valor == 2:
            duracao_segundos = 86400 * 1
        else:
            duracao_segundos = 86400 * dias_valor
            
        tempo_expiracao = time.time() + duracao_segundos
        
        collection_clientes.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "nome": "Adicionado Manualmente",
                    "expira_em": tempo_expiracao,
                    "aviso_1dia_enviado": False,
                    "aviso_20min_enviado": False
                }
            },
            upsert=True
        )
        await update.message.reply_text(f"✅ Usuário `{user_id}` adicionado com sucesso no plano correspondente a `{dias_valor}`!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao adicionar usuário: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("cfg_chat_"):
        chat_id_str = data.replace("cfg_chat_", "")
        chat_data = collection_chats.find_one({"chat_id": int(chat_id_str)})
        
        if not chat_data:
            try:
                await query.answer("❌ Chat não encontrado no banco de dados.", show_alert=True)
            except Exception:
                pass
            return
            
        try:
            await query.answer()
        except Exception:
            pass
            
        title = chat_data.get("title", "Desconhecido")
        chat_id = chat_data["chat_id"]
        tipo = chat_data.get("type", "grupo")
        
        texto_cfg = (
            f"⚙️ **Configuração do Chat**\n\n"
            f"📌 **Nome:** {title}\n"
            f"📂 **Tipo:** {tipo}\n"
            f"🆔 **ID Oficial:** `{chat_id}`\n\n"
            f"👇 Clique no botão abaixo para copiar o ID ou usá-lo na variável do bot:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 Copiar ID do Chat", copy_text=dict(text=str(chat_id)))],
            [InlineKeyboardButton("🔙 Voltar aos Chats", callback_data="cfg_voltar_lista")]
        ]
        
        try:
            await query.edit_message_text(texto_cfg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            pass
        return

    elif data == "cfg_voltar_lista":
        try:
            await query.answer()
        except Exception:
            pass
            
        chats = list(collection_chats.find({}))
        if not chats:
            try:
                await query.edit_message_text("⚙️ Nenhum chat catalogado no momento.", parse_mode="Markdown")
            except Exception:
                pass
            return

        keyboard = []
        for chat in chats:
            chat_id = chat["chat_id"]
            title = chat["title"] or f"Chat {chat_id}"
            tipo = chat.get("type", "grupo")
            emoji = "📢" if tipo == "channel" else "👥"
            keyboard.append([InlineKeyboardButton(f"{emoji} {title}", callback_data=f"cfg_chat_{chat_id}")])

        try:
            await query.edit_message_text(
                "⚙️ **Painel de Configuração de Grupos/Canais**\n\n"
                "Selecione abaixo o canal ou grupo que deseja gerenciar:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception:
            pass
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
                
                duracao_segundos = 86400  
                if valor_pago == 7.0:
                    duracao_segundos = 86400 * 7
                elif valor_pago == 20.0:
                    duracao_segundos = 86400 * 30
                elif valor_pago == 60.0:
                    duracao_segundos = 86400 * 365 * 10  
                
                user_id = update.effective_user.id
                tempo_expiracao = time.time() + duracao_segundos
                
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

async def gerenciador_assinaturas(application):
    await asyncio.sleep(10)  
    while True:
        try:
            agora = time.time()
            clientes = collection_clientes.find({})

            for cliente in clientes:
                user_id = cliente["user_id"]
                expira_em = cliente["expira_em"]
                tempo_restante = expira_em - agora

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
                    
                    collection_clientes.delete_one({"user_id": user_id})

        except Exception as e:
            print(f"Erro no gerenciador: {e}")

        await asyncio.sleep(60)  

def run_background_loop(application):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gerenciador_assinaturas(application))

def main():
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    threading.Thread(target=run_background_loop, args=(app,), daemon=True).start()

    app.add_handler(TypeHandler(Update, interceptador_universal), group=-1)
    app.add_handler(ChatMemberHandler(verificar_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("teste", teste_cmd))
    app.add_handler(CommandHandler("comandos", comandos_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("clientes", clientes_cmd))
    app.add_handler(CommandHandler("config", config_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler(["suport", "suporte"], suporte_cmd))
    app.add_handler(CommandHandler("addusuario", addusuario_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))    
    
    print("𝐓𝐎 𝐎𝐍 𝐁𝐁 😗")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
