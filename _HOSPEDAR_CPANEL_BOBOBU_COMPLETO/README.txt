BOBOBU COMPLETO - SITE + CODIGOS

O que tem aqui:
- index.php: pagina inicial BOBOBU com formulario moderno.
- api/leads.php: API que recebe mensagens do site e entrega ao projeto principal.
- favicon.ico, assets/favicon.svg e assets/logo.svg: identidade visual nova do BOBOBU.
- codigos/: ferramenta separada para codigos de email Amazon.

Como hospedar:
1. Crie public_html se ela nao existir.
2. Envie/extrai este pacote dentro de public_html.
3. A raiz ja vai com config.php pronto para o site.
4. Se quiser gerar outro token depois, copie config.example.php para config.php e troque site_admin_token.
5. No projeto principal, ferramenta "Leads Site":
   URL: https://seudominio.com
   Token: mesmo site_admin_token do config.php.
   Se usar bobobu.com.br, o projeto local ja foi configurado com o token gerado.

Se https://seudominio.com/favicon.ico mostrar tela antiga:
- apague o favicon.ico antigo no public_html;
- envie este favicon.ico novo;
- depois abra em aba anonima ou use Ctrl+F5, porque navegador guarda favicon em cache.

Formulario da pagina inicial:
- A pessoa precisa preencher pelo menos um contato: WhatsApp, Telegram ou Discord.
- Numero do ultimo pedido e opcional.
- Descricao e obrigatoria. Use a descricao para a pessoa dizer onde encontrou voce.
- Ao enviar, o site mostra: "Recebido. Em breve entrarei em contato."

Anti-spam aplicado:
- token de formulario por sessao;
- tempo minimo antes do envio;
- limite por IP;
- bloqueio de envio duplicado;
- campo invisivel contra robo simples;
- tamanho maximo do envio.

Para a ferramenta de codigos:
1. Este pacote ja inclui codigos/config.php configurado a partir do arquivo que voce enviou.
2. Se quiser mudar depois, edite public_html/codigos/config.php.
4. No projeto principal, ferramenta "Codigos":
   URL: https://seudominio.com/codigos
   Token: mesmo admin_api_token.

Importante:
- Como agora o ZIP inclui codigos/config.php real, ele tem dados sensiveis.
- Nao compartilhe este ZIP com ninguem.

Melhorias do painel de codigos:
- limpa automaticamente logs antigos e acessos expirados/revogados;
- guarda historico por codigo temporario quando possivel;
- mostra no projeto principal resumo, filtros de logs e historico do acesso selecionado.

Seguranca:
- Nao coloque senha, tokens ou contatos pessoais no index.php.
- A pasta data tem .htaccess para bloquear acesso publico.
- Use HTTPS.
- Depois de configurar /codigos, apague codigos/tools do servidor.
