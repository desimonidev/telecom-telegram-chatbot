import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ⚠️ NUNCA commite o token. Use variável de ambiente.
TOKEN = os.getenv("TELEGRAM_TOKEN", "9150648433:AAE01cAPSmSFOhkKCRQbvDTPAPxGzpUeJ8k")

BOLETO_PDF = "20.11.2026 - 1 - NOME_DO_CLIENTE - BOLETO.pdf"
NF_PDF = "20.11.2026 - 1 - NOME_DO_CLIENTE - NF.pdf"


def menu_keyboard() -> InlineKeyboardMarkup:
    """Monta o teclado do menu principal (reutilizado em vários lugares)."""
    keyboard = [
        [InlineKeyboardButton("1 - Segunda via da fatura", callback_data="segunda_via")],
        [InlineKeyboardButton("2 - Contestar fatura", callback_data="contestar")],
        [InlineKeyboardButton("3 - Contratar novos produtos", callback_data="contratar")],
        [InlineKeyboardButton("4 - Sugestão", callback_data="sugestao")],
        [InlineKeyboardButton("5 - Falar com atendente", callback_data="atendente")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("modo", None)
    await update.message.reply_text(
        "Olá! Bem-vindo ao atendimento da Provedora X.\nEscolha uma opção:",
        reply_markup=menu_keyboard(),
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "segunda_via":
        await query.message.reply_text("Enviando sua segunda via...")
        with open(BOLETO_PDF, "rb") as boleto:
            await query.message.reply_document(document=boleto, filename="boleto.pdf")
        with open(NF_PDF, "rb") as nf:
            await query.message.reply_document(document=nf, filename="nota_fiscal.pdf")
        await perguntar_se_ajuda_mais(
            query.message, "Pronto! Enviamos seu boleto e sua nota fiscal."
        )

    elif query.data == "contestar":
        context.user_data["modo"] = "contestacao"
        await query.message.reply_text(
            "Entendi. Por favor, descreva o problema com sua fatura "
            "(ex: 'minha fatura veio mais cara')."
        )

    elif query.data == "contratar":
        await query.message.reply_text(
            "Produtos mais procurados:\n"
            "• Internet 500MB — R$ 99,90\n"
            "• Internet 1GB — R$ 129,90\n"
            "• Combo TV + Internet — R$ 189,90\n\n"
            "Um atendente entrará em contato para fechar o pedido."
        )

    elif query.data == "sugestao":
        context.user_data["modo"] = "sugestao"
        await query.message.reply_text("Adoramos ouvir você! Digite sua sugestão:")

    elif query.data == "atendente":
        await query.message.reply_text(
            "Um atendente humano vai te responder em breve. Horário: seg-sex, 8h às 18h."
        )

    elif query.data == "ajuda_sim":
        await query.message.reply_text(
            "Claro! Escolha uma opção:", reply_markup=menu_keyboard()
        )

    elif query.data == "ajuda_nao":
        await query.message.reply_text(
            "Tudo bem! Obrigado pelo contato. Se precisar, digite /start. 👋"
        )


async def texto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modo = context.user_data.pop("modo", None)
    texto = update.message.text.lower()

    if modo == "contestacao":
        if any(p in texto for p in ["mais cara", "aumentou", "caro", "subiu"]):
            resposta = (
                "Sua fatura pode ter sofrido reajuste anual. "
                "Verifique o aviso de reajuste enviado no mês anterior."
            )
        elif any(
            p in texto
            for p in ["não contratei", "nao contratei", "indevido", "cobrança indevida"]
        ):
            resposta = "Vamos verificar os serviços cobrados. Um atendente entrará em contato."
        else:
            resposta = "Entendi. Para agilizar, um atendente vai analisar seu caso."

        await perguntar_se_ajuda_mais(update.message, resposta)

    elif modo == "sugestao":
        await perguntar_se_ajuda_mais(
            update.message, "Obrigado pela sugestão! Vamos registrar para a equipe."
        )

    else:
        await update.message.reply_text(
            "⚠️ Por favor, utilize as opções do menu abaixo:",
            reply_markup=menu_keyboard(),
        )


async def comando_desconhecido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ Comando não reconhecido. Por favor, utilize as opções do menu:",
        reply_markup=menu_keyboard(),
    )


async def perguntar_se_ajuda_mais(message, texto_anterior: str):
    keyboard = [
        [
            InlineKeyboardButton("✅ Sim", callback_data="ajuda_sim"),
            InlineKeyboardButton("❌ Não", callback_data="ajuda_nao"),
        ]
    ]
    await message.reply_text(
        f"{texto_anterior}\n\nTe ajudo em algo mais?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def main():
    app = Application.builder().token(TOKEN).build()

    # Ordem importa: /start ANTES do fallback de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.COMMAND, comando_desconhecido))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_handler))

    print("Bot rodando... Ctrl+C para parar.")
    app.run_polling()


if __name__ == "__main__":
    main()