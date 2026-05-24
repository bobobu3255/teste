PAINEL DE CODIGOS DE EMAIL - CPANEL/TITAN

Objetivo:
Mostrar apenas codigos recebidos no email central, com login e atualizacao automatica.

Como usar:
1. No Titan, crie ou escolha um email central, por exemplo:
   codigos@seudominio.com

2. Configure encaminhamento nos emails que voce quer monitorar:
   amazon1@seudominio.com -> codigos@seudominio.com
   amazon2@seudominio.com -> codigos@seudominio.com

3. No cPanel, crie uma pasta, por exemplo:
   public_html/codigos

4. Envie todos os arquivos desta pasta para public_html/codigos.

5. Copie config.example.php para config.php.

6. Abra no navegador:
   https://seudominio.com/codigos/tools/gerar_hash.php

7. Gere a senha do painel e copie estes 3 campos para config.php:
   panel_password_hash
   admin_api_token
   app_secret

8. Em config.php, coloque:
   username = codigos@seudominio.com
   password = senha do email central Titan
   admin_api_token = um token grande para o projeto principal controlar o painel

9. No projeto principal, configure:
   URL: https://seudominio.com/codigos
   Token: o mesmo admin_api_token

Painel no navegador:
- Link publico para a pessoa: https://seudominio.com/codigos
- O admin web vem desativado por padrao.
- Crie/revogue acessos e veja logs pelo projeto principal, usando a ferramenta Codigos.
- Se algum dia quiser reativar admin no navegador, coloque web_admin_enabled = true no config.php.
- Por padrao o site mostra so os 3 codigos mais recentes do assunto "amazon.com: Tentativa de login".
- Cada codigo recebido aparece por 10 minutos com contagem regressiva.
- O email de destino aparece censurado, por exemplo: bob*****55@bobobu.com.br.

Como funciona o acesso da pessoa:
- A pessoa nao usa login e senha fixos.
- Voce cria um codigo temporario no painel admin.
- Voce define em quantos minutos ele expira.
- O tempo do acesso comeca quando a pessoa usa o codigo pela primeira vez.
- Enquanto ela usa a tela, a janela de tempo e renovada sem gastar visualizacoes extras.
- Por seguranca, o acesso fica preso ao primeiro IP e ao primeiro navegador que usar o codigo.
- Voce define quantas vezes a pessoa pode abrir/ver os codigos.
- Quando a pessoa clica em Copiar, o evento aparece nos logs do painel e da ferramenta Codigos no projeto.
- Se quiser, trava o codigo para um IP especifico.
- O sistema registra horario, IP, evento e quantidade de codigos vistos.

10. Depois que funcionar, apague a pasta tools do servidor.
    Ela serve so para instalacao/teste e nao precisa ficar online.

Configuracao Titan IMAP:
- Servidor: imap.titan.email
- Porta: 993
- Criptografia: SSL/TLS

Seguranca:
- Use apenas com emails e contas que voce controla.
- Nao compartilhe senha do email central.
- Use HTTPS.
- Crie uma senha forte para o painel.
- Apague tools/gerar_hash.php depois de gerar a senha.

Se der erro "extensao IMAP nao esta ativa":
No cPanel procure "Select PHP Version" ou "PHP Extensions" e ative "imap".
Se nao aparecer, peca ao suporte da hospedagem para ativar PHP IMAP.
