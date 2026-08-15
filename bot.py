import os
import uuid
import time
import asyncio
import requests
import threading
import random
import re
from datetime import datetime, timezone, timedelta
from flask import Flask
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaVideo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    TypeHandler,
    ContextTypes,
    ApplicationHandlerStop,
    ChatMemberHandler
)

# ---------------------- SERVIDOR WEB ----------------------
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "SanizinhaBot está online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# ---------------------- CONFIGURAÇÕES ----------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
DONO_ID = int(os.environ.get("DONO_ID", 0))
CANAL_ALVO_ID = int(os.environ.get("CANAL_ALVO_ID", 0))
MONGO_URI = os.environ.get("MONGO_URI")

LISTA_VIDEOS_START = [
    "BAACAgEAAxkBAAIKaGp9N1YMF5wDznBldvJMRfiAvS3-AAKaCAAC4ALwR3yGzFSbu90gPQQ",
    "BAACAgEAAxkBAAIKa2p9N25ckdcn_nkmXOfF01hqq9uqAAKbCAAC4ALwRygBVGmm6XmkPQQ",
    "BAACAgEAAxkBAAIKbWp9N2-Il0F069xbtF2cddqmGHRCAAKdCAAC4ALwRzHzdov_dPkAAT0E",
    "BAACAgEAAxkBAAIKbmp9N3KubAJB7y7VUkXmAWYCx7RUAAKeCAAC4ALwR_uMlI_0xgdGPQQ",
    "BAACAgEAAxkBAAIKb2p9N345FfCVPZjj69zQ_AABBM4yswACnwgAAuAC8EcqG-GV1ULfbD0E",
    "BAACAgEAAxkBAAIKcGp9ONjrHy7m0fU7_p5NhIS6eqnVAAKgCAAC4ALwR4kWQWnHxDENPQQ",
    "BAACAgEAAxkBAAIKcWp9ONuT3vY1Gesd3gSxGgABIT812AACoQgAAuAC8EfnTbiy5ulkvT0E"
]

# Conexão Banco de Dados
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000, tlsAllowInvalidCertificates=True)
    db = mongo_client["sanizinhabot_db"]
    collection_clientes = db["clientes"]
    collection_chats = db["chats_autorizados"]
except Exception as e:
    print(f"Erro ao conectar MongoDB: {e}")

# Variáveis Globais
TEMPO_INICIAL = time.time()
FUSO_RJ = timezone(timedelta(hours=-3))
ULTIMO_COMANDO = {}
CONTADOR_AVISOS_FLOD = {}
BLOQUEIO_FLOD = {}
TEMPO_LIMITE_COMANDO = 2
MAX_AVISOS_FLOD = 5
TEMPO_BLOQUEIO_FLOD = 600
pagamentos_notificados = set()

# ---------------------- FUNÇÕES AUXILIARES ----------------------
def eh_cliente_ativo(user_id: int) -> bool:
    if user_id == DONO_ID:
        return True
    cli = collection_clientes.find_one({"user_id": user_id})
    return bool(cli and cli.get("expira_em", 0) > time.time())

def formatar_tempo_restante(segundos):
    if segundos <= 0:
        return "Expirado"
    if segundos >= 315360000:
        return "Permanente"
    dias = int(segundos // 86400)
    horas = int((segundos % 86400) // 3600)
    minutos = int((segundos % 3600) // 60)
    partes = []
    if dias > 0:
        partes.append(f"{dias}d")
    if horas > 0:
        partes.append(f"{horas}h")
    if minutos > 0:
        partes.append(f"{minutos}m")
    return " ".join(partes) if partes else "Menos de 1 minuto"

def formatar_data_rj(timestamp):
    return datetime.fromtimestamp(timestamp, tz=FUSO_RJ).strftime("%d/%m/%Y às %H:%M")

# ---------------------- COMANDOS DO DONO ----------------------
async def pegarid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    mensagem = update.message
    if mensagem.reply_to_message and mensagem.reply_to_message.video:
        video = mensagem.reply_to_message.video
        await mensagem.reply_text(f"✅ FILE_ID DO VÍDEO:\n\n`{video.file_id}`\nDuração: {video.duration}s", parse_mode="Markdown")
        return
    if mensagem.video:
        await mensagem.reply_text(f"✅ FILE_ID DO VÍDEO:\n\n`{mensagem.video.file_id}`\nDuração: {mensagem.video.duration}s", parse_mode="Markdown")
        return
    await mensagem.reply_text("⚠️ Responda um vídeo com /pegarid OU envie um vídeo para eu pegar o código!")

async def clientes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    agora = time.time()
    clientes = list(collection_clientes.find({}))
    if not clientes:
        await update.message.reply_text("📭 Nenhum cliente cadastrado no momento.")
        return
    
    texto = f"📋 LISTA DE CLIENTES ATIVOS ({len(clientes)}):\n⏰ Dados atualizados em tempo real!\n\n"
    for idx, cli in enumerate(clientes, 1):
        user_id = cli.get("user_id")
        expira_em = cli.get("expira_em", 0)
        tempo_restante = expira_em - agora
        tempo_str = formatar_tempo_restante(tempo_restante)
        
        nome_atual = "❌ Não carregado"
        username_atual = "Sem @"
        try:
            usuario = await context.bot.get_chat(user_id)
            nome_atual = f"{usuario.first_name or ''} {usuario.last_name or ''}".strip() or "Sem nome"
            username_atual = f"@{usuario.username}" if usuario.username else "Sem @"
            collection_clientes.update_one({"user_id": user_id}, {"$set": {"nome": nome_atual, "username": username_atual}})
        except:
            nome_atual = cli.get("nome", "Sem nome")
            username_atual = cli.get("username", "Sem @")
        
        valor_pago = cli.get("valor_pago", "Sem registro")
        data_compra_ts = cli.get("data_compra")
        data_compra = formatar_data_rj(data_compra_ts) if data_compra_ts else "Sem registro"
        data_expira = "♾️ PERMANENTE" if tempo_str == "Permanente" else formatar_data_rj(expira_em)

        texto += (
            f"🔹 {idx}. {nome_atual}\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Usuário: {username_atual}\n"
            f"💰 Valor Pago: R$ {valor_pago}\n"
            f"📅 Pagamento: {data_compra}\n"
            f"⏳ Restante: {tempo_str}\n"
            f"📆 Expira em: {data_expira}\n\n"
        )
    await update.message.reply_text(texto)

# ---------------------- PROTEÇÃO E BLOQUEIO ----------------------
async def interceptador_universal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user
    if not usuario or usuario.id == DONO_ID:
        return
    user_id = usuario.id
    agora = time.time()

    if user_id in BLOQUEIO_FLOD:
        if BLOQUEIO_FLOD[user_id] > agora:
            raise ApplicationHandlerStop
        else:
            del BLOQUEIO_FLOD[user_id]
            CONTADOR_AVISOS_FLOD.pop(user_id, None)

    if update.message and update.message.text and update.message.text.startswith("/"):
        comando = update.message.text.split()[0].split("@")[0].lower()
        if comando in ["/start", "/suporte", "/suport"]:
            if user_id not in ULTIMO_COMANDO:
                ULTIMO_COMANDO[user_id] = {}
            ultimo_envio = ULTIMO_COMANDO[user_id].get(comando, 0)
            if agora - ultimo_envio < TEMPO_LIMITE_COMANDO:
                CONTADOR_AVISOS_FLOD[user_id] = CONTADOR_AVISOS_FLOD.get(user_id, 0) + 1
                avisos = CONTADOR_AVISOS_FLOD[user_id]
                if avisos >= MAX_AVISOS_FLOD:
                    BLOQUEIO_FLOD[user_id] = agora + TEMPO_BLOQUEIO_FLOD
                    CONTADOR_AVISOS_FLOD[user_id] = 0
                    await context.bot.send_message(user_id, "🚫 Bloqueado temporariamente! Não envie comandos rápido demais, aguarde 10 minutos.")
                else:
                    await context.bot.send_message(user_id, "⚠️ Devagar! Não envie comandos tão rápido, ou será bloqueado.")
                raise ApplicationHandlerStop
            ULTIMO_COMANDO[user_id][comando] = agora
            return
        raise ApplicationHandlerStop

async def bloquear_nao_pagantes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    membro = update.chat_member
    if not membro or membro.chat.id != CANAL_ALVO_ID:
        return
    usuario = membro.new_chat_member.user
    if membro.new_chat_member.status == "member" and not eh_cliente_ativo(usuario.id):
        try:
            await context.bot.send_message(usuario.id, "❌ ACESSO NEGADO!\nPara entrar no grupo compre um plano pelo comando /start")
            await context.bot.ban_chat_member(CANAL_ALVO_ID, usuario.id)
            await context.bot.unban_chat_member(CANAL_ALVO_ID, usuario.id)
        except Exception as e:
            print(f"Erro ao remover usuário: {e}")

async def verificar_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = update.my_chat_member
    if not resultado:
        return
    chat = resultado.chat
    status = resultado.new_chat_member.status
    if chat.type in ["group", "supergroup", "channel"]:
        if status in ["member", "administrator"]:
            collection_chats.update_one({"chat_id": chat.id}, {"$set": {"chat_id": chat.id, "titulo": chat.title, "tipo": chat.type}}, upsert=True)
        elif status in ["left", "kicked"]:
            collection_chats.delete_one({"chat_id": chat.id})

# ---------------------- MENU PRINCIPAL ----------------------
async def enviar_menu_start(mensagem, bot):
    texto = "𝗧𝗢𝗗𝗢𝗦 𝗢𝗦 𝗖𝗢𝗡𝗧𝗘𝗨𝗗𝗢𝗦 𝗩𝗔𝗭𝗔𝗗0𝗦🤫 𝗗𝗢 𝗠𝗢𝗠𝗘𝗡𝗧𝗢🥵\n\nEscolha seu plano VIP abaixo:"
    botoes = [
        [InlineKeyboardButton("1 HORA → R$ 2,00🔥", callback_data="comprar_2.00")],
        [InlineKeyboardButton("1 DIA → R$ 5,00", callback_data="comprar_5.00")],
        [InlineKeyboardButton("1 SEMANA → R$ 10,00", callback_data="comprar_10.00")],
        [InlineKeyboardButton("1 MÊS → R$ 30,00", callback_data="comprar_30.00")],
        [InlineKeyboardButton("💎 PERMANENTE → R$ 55,00", callback_data="comprar_55.00")],
        [InlineKeyboardButton("𝑷𝑹𝑬𝑽𝑰𝑨𝑺 𝑮𝑹𝑨𝑻𝑰𝑺🔥", url="https://t.me/+Qmozi6YQ5dE1MDYx")]
    ]
    try:
        await bot.edit_message_media(
            media=InputMediaVideo(media=random.choice(LISTA_VIDEOS_START), caption=texto),
            chat_id=mensagem.chat.id,
            message_id=mensagem.message_id,
            reply_markup=InlineKeyboardMarkup(botoes)
        )
    except:
        await bot.edit_message_text(texto, chat_id=mensagem.chat.id, message_id=mensagem.message_id, reply_markup=InlineKeyboardMarkup(botoes))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    texto = "𝗧𝗢𝗗𝗢𝗦 𝗢𝗦 𝗖𝗢𝗡𝗧𝗘𝗨𝗗𝗢𝗦 𝗩𝗔𝗭𝗔𝗗0𝗦🤫 𝗗𝗢 𝗠𝗢𝗠𝗘𝗡𝗧𝗢🥵\n\nEscolha seu plano VIP abaixo:"
    botoes = [
        [InlineKeyboardButton("1 HORA → R$ 2,00🔥", callback_data="comprar_2.00")],
        [InlineKeyboardButton("1 DIA → R$ 5,00", callback_data="comprar_5.00")],
        [InlineKeyboardButton("1 SEMANA → R$ 10,00", callback_data="comprar_10.00")],
        [InlineKeyboardButton("1 MÊS → R$ 30,00", callback_data="comprar_30.00")],
        [InlineKeyboardButton("💎 PERMANENTE → R$ 55,00", callback_data="comprar_55.00")],
        [InlineKeyboardButton("𝑷𝑹𝑬𝑽𝑰𝑨𝑺 𝑮𝑹𝑨𝑻𝑰𝑺🔥", url="https://t.me/+Qmozi6YQ5dE1MDYx")]
    ]
    try:
        await update.message.reply_video(
            video=random.choice(LISTA_VIDEOS_START),
            caption=texto,
            reply_markup=InlineKeyboardMarkup(botoes),
            protect_content=True
        )
    except:
        await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(botoes))

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    chat = update.effective_chat
    usuario = update.effective_user
    await update.message.reply_text(f"📌 DADOS:\n\nChat: {chat.title or 'Privado'}\nID Chat: `{chat.id}`\nSeu Nome: {usuario.first_name}\nSeu ID: `{usuario.id}`", parse_mode="Markdown")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DONO_ID:
        return
    inicio = time.time()
    msg = await update.message.reply_text("🔄 Verificando latência...")
    latencia = int((time.time() - inicio) * 1000)
    tempo_online = int(time.time() - TEMPO_INICIAL)
    await msg.edit_text(f"✅ PONG!\nLatência: {latencia}ms\nOnline há: {tempo_online//3600}h {(tempo_online%3600)//60}m")

async def suporte_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 Suporte e dúvidas: @Lyhhxv")

# ---------------------- PAGAMENTOS E BOTÕES ----------------------
async def gerar_pagamento(valor, usuario):
    url = "https://api.mercadopago.com/v1/payments"
    cabecalhos = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }
    dados = {
        "transaction_amount": valor,
        "description": f"Assinatura VIP - R${valor:.2f}",
        "payment_method_id": "pix",
        "payer": {
            "email": f"user_{usuario.id}@botvip.com",
            "first_name": usuario.first_name or "Cliente",
            "last_name": usuario.last_name or "VIP"
        }
    }
    try:
        resposta = requests.post(url, json=dados, headers=cabecalhos, timeout=15)
        if resposta.status_code == 201:
            dados_pag = resposta.json()
            return True, dados_pag["id"], dados_pag["point_of_interaction"]["transaction_data"]["qr_code"]
        return False, None, f"Erro {resposta.status_code}"
    except Exception as e:
        return False, None, str(e)

async def verificar_pagamento(pag_id):
    cabecalhos = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    try:
        resposta = requests.get(f"https://api.mercadopago.com/v1/payments/{pag_id}", headers=cabecalhos, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json()
            return dados.get("status") == "approved", dados.get("transaction_amount", 0)
        return False, 0
    except Exception as e:
        print(f"Erro verificar pagamento: {e}")
        return False, 0

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dados = query.data

    if dados.startswith("comprar_"):
        valor = float(dados.split("_")[1])
        await query.edit_message_text("⏳ Gerando código PIX... Aguarde um instante!", reply_markup=None)
        usuario = update.effective_user
        ok, pag_id, qr = await gerar_pagamento(valor, usuario)
        if ok:
            botoes = [
                [InlineKeyboardButton("📋 Copiar Código PIX", copy_text={"text": qr})],
                [InlineKeyboardButton("✅ Verificar Pagamento", callback_data=f"check_{pag_id}")],
                [InlineKeyboardButton("🔄 Voltar aos Planos", callback_data="ver_outros_precos")]
            ]
            await query.edit_message_text(
                f"💳 PIX GERADO COM SUCESSO!\n\n"
                f"💵 Valor: R$ {valor:.2f}\n\n"
                f"📌 Código Copia e Cola:\n`{qr}`\n\n"
                f"⚠️ Após pagar clique no botão ✅ Verificar",
                reply_markup=InlineKeyboardMarkup(botoes),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(f"❌ Erro ao gerar pagamento: {qr}")

    elif dados.startswith("check_"):
        pag_id = dados.split("_")[1]
        aprovado, valor_pago = await verificar_pagamento(pag_id)
        if aprovado:
            await query.answer("✅ PAGAMENTO APROVADO! ACESSO LIBERADO!", show_alert=True)
            # DURAÇÕES EXATAS QUE VOCÊ PEDIU
            if abs(valor_pago - 2.00) < 0.01:
                duracao_seg = 3600
                nome_plano = "1 Hora"
            elif abs(valor_pago - 5.00) < 0.01:
                duracao_seg = 86400
                nome_plano = "1 Dia"
            elif abs(valor_pago - 10.00) < 0.01:
                duracao_seg = 86400 * 7
                nome_plano = "1 Semana"
            elif abs(valor_pago - 30.00) < 0.01:
                duracao_seg = 86400 * 30
                nome_plano = "1 Mês"
            elif abs(valor_pago - 55.00) < 0.01:
                duracao_seg = 315360000
                nome_plano = "Permanente / Vitalício"
            else:
                duracao_seg = int(valor_pago * 86400)
                nome_plano = f"R$ {valor_pago:.2f}"

            user_id = update.effective_user.id
            data_expira = time.time() + duracao_seg
            usuario_obj = update.effective_user
            username = f"@{usuario_obj.username}" if usuario_obj.username else "Sem @"

            # Salva no banco
            collection_clientes.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "nome": usuario_obj.first_name or "Cliente",
                        "username": username,
                        "expira_em": data_expira,
                        "valor_pago": f"{valor_pago:.2f}",
                        "data_compra": time.time(),
                        "aviso_1dia": False,
                        "aviso_20min": False
                    }
                },
                upsert=True
            )

            # Cria link do grupo
            link_grupo = None
            if CANAL_ALVO_ID != 0:
                try:
                    link_grupo = (await context.bot.create_chat_invite_link(
                        chat_id=CANAL_ALVO_ID,
                        member_limit=1,
                        expire_date=int(time.time()) + 86400
                    )).invite_link
                except:
                    pass

            # Edita mensagem com sucesso
            await query.edit_message_text(
                f"✅ PAGAMENTO APROVADO!\n\n"
                f"📦 Plano: {nome_plano}\n"
                f"💵 Valor Pago: R$ {valor_pago:.2f}\n"
                f"🔗 Link do Grupo: {link_grupo or 'Contate @Lyhhxv'}\n\n"
                f"Aproveite muito o conteúdo 🩷"
            )

            # Avisa o dono uma única vez
            if pag_id not in pagamentos_notificados:
                pagamentos_notificados.add(pag_id)
                relatorio = (
                    "✅ NOVA VENDA REGISTRADA!\n\n"
                    f"Cliente: {usuario_obj.first_name or 'Sem nome'}\n"
                    f"Usuário: {username}\n"
                    f"ID: `{user_id}`\n"
                    f"Valor: R$ {valor_pago:.2f}\n"
                    f"Plano: {nome_plano}\n"
                    f"Expira em: {formatar_data_rj(data_expira) if nome_plano != 'Permanente / Vitalício' else '♾️ NUNCA'}"
                )
                try:
                    await context.bot.send_message(chat_id=DONO_ID, text=relatorio, parse_mode="Markdown")
                except:
                    pass
        else:
            await query.answer("⏳ AINDA NÃO FOI PAGO! Faça o Pix e clique novamente!", show_alert=True)
            await query.edit_message_text("⏳ Aguardando pagamento...\n\nFaça o pagamento do PIX acima e clique novamente no botão ✅")

    elif dados == "ver_outros_precos":
        await enviar_menu_start(query.message, context.bot)

# ---------------------- GERENCIADOR DE ASSINATURAS ----------------------
async def gerenciador_assinaturas(app):
    await asyncio.sleep(10)
    while True:
        agora = time.time()
        for cliente in collection_clientes.find({}):
            user_id = cliente["user_id"]
            expira_em = cliente["expira_em"]
            tempo_restante = expira_em - agora

            # Avisa 1 dia antes
            if 82800 <= tempo_restante <= 86400 and not cliente.get("aviso_1dia"):
                botoes = [[InlineKeyboardButton("Renovar Agora", callback_data="ver_outros_precos")]]
                await app.bot.send_message(chat_id=user_id, text="⚠️ SEU PLANO VENCE AMANHÃ! Renove antes que perca o acesso!", reply_markup=InlineKeyboardMarkup(botoes))
                collection_clientes.update_one({"user_id": user_id}, {"$set": {"aviso_1dia": True}})
            
            # Avisa 20 minutos antes
            elif 0 < tempo_restante <= 1200 and not cliente.get("aviso_20min"):
                botoes = [[InlineKeyboardButton("Renovar AGORA", callback_data="ver_outros_precos")]]
                await app.bot.send_message(chat_id=user_id, text="🚨 ATENÇÃO: SEU PLANO VENCE EM 20 MINUTOS! Renove imediatamente!", reply_markup=InlineKeyboardMarkup(botoes))
                collection_clientes.update_one({"user_id": user_id}, {"$set": {"aviso_20min": True}})
            
            # Remove se venceu
            elif tempo_restante <= 0 and CANAL_ALVO_ID != 0:
                try:
                    await app.bot.kick_chat_member(chat_id=CANAL_ALVO_ID, user_id=user_id)
                    await app.bot.unban_chat_member(chat_id=CANAL_ALVO_ID, user_id=user_id)
                except:
                    pass
                collection_clientes.delete_one({"user_id": user_id})
        await asyncio.sleep(60)

def run_background(app):
    asyncio.new_event_loop().run_until_complete(gerenciador_assinaturas(app))

# ---------------------- INICIALIZAÇÃO ----------------------
def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    threading.Thread(target=run_background, args=(app,), daemon=True).start()

    # Adiciona todos os handlers
    app.add_handler(TypeHandler(Update, interceptador_universal), group=-1)
    app.add_handler(ChatMemberHandler(bloquear_nao_pagantes))
    app.add_handler(ChatMemberHandler(verificar_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("suporte", suporte_cmd))
    app.add_handler(CommandHandler("suport", suporte_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("pegarid", pegarid_cmd))
    app.add_handler(CommandHandler("clientes", clientes_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ BOT INICIADO COM SUCESSO! Tudo funcionando + edita mensagens!")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    asyncio.run(main())
