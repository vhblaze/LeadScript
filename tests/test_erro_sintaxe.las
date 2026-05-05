lead = extrair_payload()
score = 90

se score > 80
    enviar_email(lead["email"], "Bem-vindo", "boas_vindas.html")
fim
