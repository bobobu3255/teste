/**
 * Crunchyroll Bot v8.3 - PROCESSAMENTO PARALELO
 * 
 * Versão com suporte a múltiplos navegadores simultâneos.
 * Cada navegador processa contas de forma independente.
 * 
 * Melhorias v8.3:
 * - Limite de 3 cartões por conta
 * - Remoção automática de contas/cartões após teste
 * - Tratamento robusto de erros (bot não para mais)
 * - Verificação de assinatura corrigida
 * 
 * @version 8.3.0
 */

import readline from 'readline';
import CONFIG from './config/settings.js';
import { colors } from './lib/helpers/logger.js';
import { Orchestrator } from './lib/orchestrator.js';

// ============================================
// CONFIGURAÇÃO
// ============================================
// Número de navegadores: via variável de ambiente ou padrão 3
const NUM_WORKERS = parseInt(process.env.NUM_WORKERS) || 3;

// ============================================
// CONTROLE DO TERMINAL
// ============================================
let orchestrator = null;

readline.emitKeypressEvents(process.stdin);
if (process.stdin.isTTY) {
  process.stdin.setRawMode(true);
}

process.stdin.on('keypress', async (str, key) => {
  if (key.name === 'p') {
    // Pausar/Resumir
    if (orchestrator) {
      console.log('\n>>> PAUSANDO/RESUMINDO WORKERS...\n');
      // Toggle pause
    }
  }
  if (key.name === 'q' || (key.ctrl && key.name === 'c')) {
    console.log('\n>>> PARANDO BOT...\n');
    if (orchestrator) {
      await orchestrator.stop();
    }
    process.exit(0);
  }
});

// ============================================
// MAIN
// ============================================
async function main() {
  console.clear();
  console.log(`
${colors.bright}${colors.cyan}╔════════════════════════════════════════════════════════════╗
║       CRUNCHYROLL BOT v${CONFIG.VERSION} - PROCESSAMENTO PARALELO        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Este bot executa ${String(NUM_WORKERS).padEnd(1)} navegador(es) simultaneamente,        ║
║  cada um processando contas de forma independente.         ║
║                                                            ║
║  Benefícios:                                               ║
║    - Velocidade ${NUM_WORKERS}x maior                                   ║
║    - Cada navegador com User-Agent diferente               ║
║    - Sistema de filas sem conflitos                        ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║  Controles:                                                ║
║    Q ou Ctrl+C = Parar todos os navegadores                ║
╚════════════════════════════════════════════════════════════╝${colors.reset}
`);
  
  console.log(`${colors.cyan}[INFO] Usando ${NUM_WORKERS} navegador(es) simultâneo(s)${colors.reset}\n`);
  
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
      console.log(`\n${colors.green}Bot finalizado com sucesso!${colors.reset}\n`);
    }
  });
  
  // Iniciar processamento paralelo
  await orchestrator.start();
  
  process.exit(0);
}

// Tratamento de erros não capturados
process.on('uncaughtException', async (err) => {
  console.error(`\n${colors.red}Erro não capturado: ${err.message}${colors.reset}\n`);
  if (orchestrator) {
    await orchestrator.stop();
  }
  process.exit(1);
});

process.on('unhandledRejection', async (reason, promise) => {
  console.error(`\n${colors.red}Promise rejeitada: ${reason}${colors.reset}\n`);
});

// Iniciar
main();
