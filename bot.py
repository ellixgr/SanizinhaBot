import os
import uuid
import time
import requests
import threading
from flask import Flask
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
DONO_ID = 805811682
LINK_DO_GRUPO = "https://t.me/+ZeYMNaaCZsdhZjMx"
GRUPO_ALVO_ID = 7711945457
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
        await context.bot.send_message(chat_id=GRUPO_ALVO_ID, text=msg_teste, parse_mode="Markdown")
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
            
            # Criando arquivo .txt com o código pix para facilitar a cópia em qualquer dispositivo
            file_path = f"pix_{payment_id}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(qr_data)
                
            keyboard_final = [
                [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_{payment_id}")]
            ]
            
            try:
                with open(file_path, "rb") as doc:
                    await query.message.reply_document(
                        document=doc,
                        filename="codigo_pix.txt",
                        caption=msg_completa,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard_final)
                    )
            except Exception:
                await query.message.reply_text(msg_completa, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard_final))
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
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
                await query.message.reply_text(
                    f"🎉 **Pagamento Aprovado com Sucesso!**\n\n"
                    f"Muito obrigado pela compra! Aqui está o seu link de acesso exclusivo:\n{LINK_DO_GRUPO}"
                )
                if payment_id not in pagamentos_notificados:
                    pagamentos_notificados.add(payment_id)
                    valor_pago = float(resp_data.get("transaction_amount", 0.0))
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
                        await context.bot.send_message(chat_id=GRUPO_ALVO_ID, text=relatorio_privado, parse_mode="Markdown")
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

def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
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
