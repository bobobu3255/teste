/**
 * Crunchyroll Login Bot v1.0.0
 * 
 * Bot que faz LOGIN em contas existentes e organiza resultados locais.
 * Diferente do bot principal que cria contas novas.
 * 
 * Suporta múltiplos navegadores simultâneos (padrão: 3).
 * 
 * CORREÇÃO v1.0.1:
 * - Bot não fecha mais imediatamente quando arquivos estão vazios
 * - Aguarda dados serem adicionados antes de iniciar
 * - Melhor tratamento de erros
 * 
 * @version 1.0.1
 */

import readline from 'readline';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import CONFIG from './config/settings.js';
import { colors, log, delay } from './lib/helpers/logger.js';
import { Orchestrator } from './lib/orchestrator.js';

// ============================================
// CONFIGURAÇÃO
// ============================================

// Número de navegadores: via variável de ambiente ou padrão 3
const NUM_WORKERS = parseInt(process.env.NUM_WORKERS) || 3;

// Diretório base
const BASE_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)));
const DATA_DIR = path.join(BASE_DIR, 'data');

// ============================================
// CONTROLE DO TERMINAL
// ============================================

let orchestrator = null;
let isRunning = true;

readline.emitKeypressEvents(process.stdin);
if (process.stdin.isTTY) {
  process.stdin.setRawMode(true);
}

process.stdin.on('keypress', async (str, key) => {
  if (key.name === 'p') {
    // Pausar/Resumir
    if (orchestrator) {
      console.log('\n>>> PAUSANDO/RESUMINDO WORKERS...\n');
    }
  }
  if (key.name === 'q' || (key.ctrl && key.name === 'c')) {
    console.log('\n>>> PARANDO BOT...\n');
    isRunning = false;
    if (orchestrator) {
      await orchestrator.stop();
    }
    process.exit(0);
  }
});

// ============================================
// FUNÇÕES AUXILIARES
// ============================================

/**
 * Verifica se há dados nos arquivos de entrada
 */
function verificarDados() {
  const contasFile = path.join(DATA_DIR, 'contas.txt');
  const cartoesFile = path.join(DATA_DIR, 'cartoes.txt');
  
  let temContas = false;
  let temCartoes = false;
  
  try {
    if (fs.existsSync(contasFile)) {
      const contas = fs.readFileSync(contasFile, 'utf8')
        .split(/\r?\n/)
        .filter(line => line.trim() && !line.startsWith('#'));
      temContas = contas.length > 0;
    }
  } catch (e) {}
  
  try {
    if (fs.existsSync(cartoesFile)) {
      const cartoes = fs.readFileSync(cartoesFile, 'utf8')
        .split(/\r?\n/)
        .filter(line => line.trim() && !line.startsWith('#'));
      temCartoes = cartoes.length > 0;
    }
  } catch (e) {}
  
  return { temContas, temCartoes };
}

/**
 * Aguarda dados serem adicionados aos arquivos
 */
async function aguardarDados() {
  console.log(`\n${colors.yellow}[AGUARDANDO] Adicione dados aos arquivos em data/:${colors.reset}`);
  console.log(`${colors.cyan}  - contas.txt (formato: email:senha ou email|senha)${colors.reset}`);
  console.log(`${colors.cyan}  - cartoes.txt opcional (controle local/manual)${colors.reset}`);
  console.log(`\n${colors.dim}Pressione Q para sair ou aguarde os dados serem adicionados...${colors.reset}\n`);
  
  let lastCheck = { temContas: false, temCartoes: false };
  
  while (isRunning) {
    const dados = verificarDados();
    
    // Mostrar status se mudou
    if (dados.temContas !== lastCheck.temContas || dados.temCartoes !== lastCheck.temCartoes) {
      const statusContas = dados.temContas ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`;
      const statusCartoes = dados.temCartoes ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`;
      console.log(`[STATUS] Contas: ${statusContas} | Cartoes locais: ${statusCartoes}`);
      lastCheck = dados;
    }
    
    if (dados.temContas) {
      console.log(`\n${colors.green}[OK] Contas encontradas! Iniciando verificador...${colors.reset}\n`);
      return true;
    }
    
    await delay(2000); // Verificar a cada 2 segundos
  }
  
  return false;
}

// ============================================
// MAIN
// ============================================

async function main() {
  console.clear();
  console.log(`
${colors.bright}${colors.cyan}╔════════════════════════════════════════════════════════════╗
║         CRUNCHYROLL LOGIN BOT v${CONFIG.VERSION}                     ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Este bot faz LOGIN em contas EXISTENTES.                  ║
║  Diferente do bot principal que cria contas novas.         ║
║                                                            ║
║  Características:                                          ║
║    - ${String(NUM_WORKERS).padEnd(1)} navegador(es) simultâneo(s)                     ║
║    - Cartoes ficam como controle local/manual              ║
║    - Contas com problema vao para revisao                  ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║  Arquivos necessários em data/:                            ║
║    - contas.txt (formato: email:senha ou email|senha)      ║
║    - cartoes.txt opcional (controle local/manual)          ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║  Controles:                                                ║
║    Q ou Ctrl+C = Parar todos os navegadores                ║
╚════════════════════════════════════════════════════════════╝${colors.reset}
`);
  
  console.log(`${colors.cyan}[INFO] Usando ${NUM_WORKERS} navegador(es) simultâneo(s)${colors.reset}\n`);
  
  // Verificar se há dados, se não, aguardar
  const dados = verificarDados();
  if (!dados.temContas) {
    const dadosOk = await aguardarDados();
    if (!dadosOk) {
      console.log(`\n${colors.yellow}[INFO] Bot encerrado pelo usuário.${colors.reset}\n`);
      process.exit(0);
    }
  }
  
  // Criar orquestrador
  orchestrator = new Orchestrator({
    numWorkers: NUM_WORKERS,
    onLog: (msg, type) => {
      // Log já é feito internamente
    },
    onStatusUpdate: (status) => {
      // Atualização de status
    },
    onComplete: (status) => {
      console.log(`\n${colors.green}Bot de Login finalizado com sucesso!${colors.reset}\n`);
    }
  });
  
  // Iniciar processamento
  try {
    await orchestrator.start();
  } catch (err) {
    console.error(`\n${colors.red}Erro ao iniciar bot: ${err.message}${colors.reset}\n`);
  }
  
  // Não sair imediatamente, aguardar mais dados ou comando do usuário
  console.log(`\n${colors.cyan}[INFO] Processamento concluído. Aguardando novos dados ou pressione Q para sair...${colors.reset}\n`);
  
  // Continuar verificando por novos dados
  while (isRunning) {
    await delay(5000);
    
    const dados = verificarDados();
    if (dados.temContas) {
      console.log(`\n${colors.green}[INFO] Novos dados detectados! Reiniciando processamento...${colors.reset}\n`);
      
      orchestrator = new Orchestrator({
        numWorkers: NUM_WORKERS,
        onComplete: (status) => {
          console.log(`\n${colors.green}Bot de Login finalizado com sucesso!${colors.reset}\n`);
        }
      });
      
      try {
        await orchestrator.start();
      } catch (err) {
        console.error(`\n${colors.red}Erro: ${err.message}${colors.reset}\n`);
      }
    }
  }
}

// Tratamento de erros não capturados
process.on('uncaughtException', async (err) => {
  console.error(`\n${colors.red}Erro não capturado: ${err.message}${colors.reset}\n`);
  console.error(err.stack);
  // Não encerrar o processo, apenas logar o erro
});

process.on('unhandledRejection', async (reason, promise) => {
  console.error(`\n${colors.red}Promise rejeitada: ${reason}${colors.reset}\n`);
  // Não encerrar o processo
});

// Iniciar
main().catch(err => {
  console.error(`\n${colors.red}Erro fatal: ${err.message}${colors.reset}\n`);
});
