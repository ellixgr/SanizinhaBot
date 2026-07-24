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
TELEGRAM_TOKEN = "8919678511:AAEzQ7m2NA2vHeA9UYXo9HxztXtursMo3oI"
MP_ACCESS_TOKEN = "APP_USR-2233798366076054-072321-1ebc8660b5623826d8e956f1d629fa98-805811682"

# ID DO DONO EXCLUSIVO (Apenas este ID pode adicionar o bot em grupos/canais)
DONO_ID = 805811682  # Atualizado para o ID proprietário da conta atual

LINK_DO_GRUPO = "https://t.me/+ZeYMNaaCZsdhZjMx"
GRUPO_ALVO_ID = 7711945457
TEMPO_INICIAL = time.time()

# FOTO ÚNICA CONFIGURADA
FOTO_START = "https://files.catbox.moe/0pw3k8.jpg"

# 𝐄𝐒𝐓𝐀𝐃𝐎𝐒 𝐄 𝐒𝐏𝐀𝐌 E ANTI-FLOOD/BAN NATURAIS
ultimo_envio = {}          
contador_spam = {}         
usuarios_bloqueados = {}     
bloqueio_temporario = {}     
pagamentos_notificados = set() 
user_last_action = {}        # Controle de anti-flood avançado para burlar limites do Telegram

async def interceptador_universal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Proteção anti-adicionamento em grupos/canais não autorizados
    chat = update.effective_chat
    user = update.effective_user
    
    if chat and chat.type in ["group", "supergroup", "channel"]:
        # Verifica se o bot foi adicionado recentemente por alguém
        # O Telegram envia my_chat_member quando o bot é adicionado a um chat
        pass

    if not user:
        return  
    user_id = user.id
    agora = time.time()

    # Sistema anti-flood e desvio de banimento por spam (Telegram Safe-Guards)
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
        
    # Intervalo inteligente dinâmico para evitar FloodWait do Telegram (Bypass Anti-Ban)
    if user_id in ultimo_envio:
        diferenca = agora - ultimo_envio[user_id]
        if diferenca < 1.2:  # Ajustado para simular comportamento humano natural e evitar bloqueio da API
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
    """Bloqueia estritamente a adição do bot em qualquer grupo ou canal por pessoas que não sejam o Dono."""
    result = update.my_chat_member
    if not result:
        return
        
    chat = result.chat
    new_status = result.new_chat_member.status
    actor = result.from_user

    # Se o bot foi adicionado a um grupo ou canal
    if chat.type in ["group", "supergroup", "channel"] and new_status in ["member", "administrator"]:
        if actor and actor.id != DONO_ID:
            try:
                # Sai imediatamente do grupo/canal não autorizado
                await context.bot.leave_chat(chat.id)
                print(f"⚠️ Bot removido automaticamente do chat {chat.id} ({chat.title}) pois o usuário {actor.id} não é o dono.")
            except Exception as e:
                print(f"Erro ao sair de chat não autorizado: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Segurança extra: comandos em chats privados evitam exposição desnecessária
    if update.effective_chat.type != "private":
        return

    texto_boas_vindas = (
        "🔥 **SEJA BEM-VINDO AO CANAL EXCLUSIVO** 🇧🇷

"
        "✨ Tenha acesso completo a todo o nosso conteúdo diário atualizado em um só lugar:

"
        "📁 +130 mil mídias disponíveis (vídeos e fotos)
"
        "🚀 Atualizações diárias sem censura
"
        "💎 Material organizado e exclusivo

"
        "👇 Escolha o seu plano abaixo para liberar o seu acesso:

"
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
        f"📊 **INFORMAÇÕES DE ID:**

"
        f"💬 **Nome do Chat:** {chat.title if chat.title else 'Privado'}
"
        f"🆔 **ID deste Chat/Grupo:** `{chat.id}`
"
        f"👤 **Seu ID de Usuário:** `{user.id}`"
    )
    await update.message.reply_text(resposta, parse_mode="Markdown")

async def teste_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    nome = user.first_name if user.first_name else "Sem nome"
    username = f"@{user.username}" if user.username else "Sem @username"
    user_id = user.id

    msg_teste = (
        f"🧪 **DADOS CAPTURADOS (COMANDO /TESTE)!** 🧪

"
        f"👤 **Nome:** {nome}
"
        f"🔗 **Username:** {username}
"
        f"🆔 **ID do Telegram:** `{user_id}`

"
        f"✅ *O bot enviou esta mensagem diretamente para o seu privado com sucesso!*"
    )
    await update.message.reply_text("✅ Teste executado! Os dados foram enviados lá no seu privado.")
    try:
        await context.bot.send_message(
            chat_id=GRUPO_ALVO_ID,
            text=msg_teste,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Erro ao enviar teste para o seu ID: {e}")

async def comandos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📜 **LISTA DE COMANDOS DO BOT** 📜

"
        "👤 **Comandos Disponíveis:**
"
        "• `/start` - Inicia o bot e exibe os planos
"
        "• `/id` - Mostra o ID exato do grupo ou chat atual
"
        "• `/teste` - Testa o envio de dados
"
        "• `/suporte` - Mostra o contato do suporte
"
        "• `/comandos` - Mostra esta lista de comandos
"
        "• `/ping` - Mostra a latência e o status da hospedagem
"
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
        f"🏓 **PONG! Informações do Sistema:**

"
        f"⚡ **Latência:** `{latencia}ms`
"
        f"⏳ **Uptime:** `{uptime_str}`
"
        f"🧠 **Memória RAM:** `512 MB (Render Cloud Gratuito)`
"
        f"💻 **CPU:** `Instância Compartilhada`
"
    )
    await msg.edit_text(resposta, parse_mode="Markdown")

async def suporte_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 **Central de Suporte**

"
        "Para tirar dúvidas ou resolver qualquer problema, entre em contato diretamente com o nosso suporte:

"
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

        # Requisição segura com tratamento de exceção para evitar quedas e bloqueios de socket
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
        except Exception as e:
            await query.message.reply_text("❌ Erro de conexão com o gateway de pagamento. Tente novamente.", parse_mode="Markdown")
            return
        
        if response.status_code == 201:
            resp_data = response.json()
            payment_id = resp_data["id"]
            qr_data = resp_data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
            
            msg_completa = (
                f"✅ **PIX Gerado com Sucesso!**

"
                f"💰 **Valor:** R$ {valor:.2f}

"
                "📋 **Código Pix Copia e Cola:**
"
                f"```
{qr_data}
```
"
            )
            keyboard_final = [
                [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_{payment_id}")]
            ]
            await query.message.reply_text(msg_completa, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard_final))
        else:
            erro_mp = response.text[:300]
            await query.message.reply_text(f"❌ Erro ao gerar o Pix:
`{erro_mp}`", parse_mode="Markdown")
            
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
            status = resp_data.get("status")       
            if status == "approved":
                try:
                    await query.answer("🎉 Pagamento Aprovado!", show_alert=True)
                except Exception:
                    pass              
                await query.message.reply_text(
                    f"🎉 **Pagamento Aprovado com Sucesso!**

"
                    f"Muito obrigado pela compra! Aqui está o seu link de acesso exclusivo:
{LINK_DO_GRUPO}"
                )
                if payment_id not in pagamentos_notificados:
                    pagamentos_notificados.add(payment_id)

                    valor_pago = float(resp_data.get("transaction_amount", 0.0))
                    
                    if valor_pago == 2.0:
                        plano_nome = "1 Dia 🔥 (R$ 2,00)"
                    elif valor_pago == 7.0:
                        plano_nome = "1 Semana (R$ 7,00)"
                    elif valor_pago == 20.0:
                        plano_nome = "1 Mês (R$ 20,00)"
                    elif valor_pago == 60.0:
                        plano_nome = "Permanente (R$ 60,00)"
                    else:
                        plano_nome = f"Personalizado (R$ {valor_pago:.2f})"

                    comprador = update.effective_user
                    nome_cliente = comprador.first_name if comprador.first_name else "Sem nome"
                    username_cliente = f"@{comprador.username}" if comprador.username else "Sem @username"
                    id_cliente = comprador.id
                    data_pagamento = time.strftime('%d/%m/%Y às %H:%M:%S', time.localtime())

                    relatorio_privado = (
                        f"🚨 **NOVA ASSINATURA CONFIRMADA!** 🚨

"
                        f"👤 **Cliente:** {nome_cliente}
"
                        f"🔗 **Username:** {username_cliente}
"
                        f"🆔 **ID do Telegram:** `{id_cliente}`
"
                        f"💰 **Valor Pago:** R$ {valor_pago:.2f}
"
                        f"📅 **Plano Escolhido:** {plano_nome}
"
                        f"⏰ **Data/Hora:** {data_pagamento}
"
                        f"🧾 **ID do Pix (Mercado Pago):** `{payment_id}`
"
                        f"🟢 **Status:** Aprovado"
                    )

                    try:
                        await context.bot.send_message(
                            chat_id=GRUPO_ALVO_ID,
                            text=relatorio_privado,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        print(f"Erro ao enviar comprovante pro seu privado: {e}")

            else:
                try:
                    await query.answer("❌ Pagamento ainda não identificado!", show_alert=True)
                except Exception:
                    pass
                await query.message.reply_text(
                    "⏳ **Pagamento ainda não identificado!**

"
                    "Realize o pagamento no app do seu banco via Pix Copia e Cola. "
                    "Se você já pagou, aguarde alguns segundos e clique no botão novamente.",
                    parse_compras="Markdown" if "parse_compras" in globals() else "Markdown"
                )
        else:
            try:
                await query.answer("❌ Erro ao consultar o Mercado Pago.", show_alert=True)
            except Exception:
                pass
            await query.message.reply_text("❌ Não foi possível verificar o pagamento no momento. Tente novamente em instantes.")

def main():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Interceptador universal com tratamento anti-flood (burlador de restrições de spam)
    app.add_handler(TypeHandler(Update, interceptador_universal), group=-1)

    # Handler restrito para impedir que qualquer outra pessoa adicione o bot em grupos/canais
    from telegram.ext import ChatMemberHandler
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
