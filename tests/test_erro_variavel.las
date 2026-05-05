lead = extrair_payload()
score = variavel_inexistente

se score > 80 entao:
    enviar_email(lead["email"], "Bem-vindo", "boas_vindas.html")
fim
