lead = extrair_payload()
score = classificar_ia(lead, "Validar se o lead e B2B")

se score > 80 entao:
    disparar_webhook("https://api.meusistema.com", lead)
    enviar_email(lead["email"], "Bem-vindo", "boas_vindas.html")
senao:
    enviar_discord("https://discord.com/api/webhooks/demo", "Lead desqualificado")
fim
