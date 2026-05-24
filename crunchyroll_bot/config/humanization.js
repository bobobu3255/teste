/**
 * @fileoverview Configurações de Humanização do Bot
 * @module config/humanization
 * @version 1.0.0
 * 
 * @description
 * Este módulo contém todas as configurações para fazer o bot parecer mais humano,
 * evitando detecção por sistemas anti-bot. Inclui delays variáveis, movimentos
 * de mouse naturais, pausas aleatórias e comportamentos realistas.
 * 
 * COMO USAR:
 * - Ajuste os valores conforme necessário
 * - Valores mais altos = mais lento mas mais seguro
 * - Valores mais baixos = mais rápido mas mais arriscado
 * 
 * @example
 * import { HUMANIZATION, getRandomDelay, shouldTakePause } from './config/humanization.js';
 */

// ============================================
// CONFIGURAÇÕES PRINCIPAIS DE HUMANIZAÇÃO
// ============================================

/**
 * Configurações de humanização do bot
 * @constant
 * @type {Object}
 */
export const HUMANIZATION = {
  /**
   * Se a humanização está habilitada globalmente
   * @type {boolean}
   */
  ENABLED: true,
  
  /**
   * Nível de humanização (1-5)
   * 1 = Mínimo (mais rápido, mais arriscado)
   * 3 = Balanceado (recomendado)
   * 5 = Máximo (mais lento, mais seguro)
   * @type {number}
   */
  LEVEL: 3,
  
  // ============================================
  // CONFIGURAÇÕES DE DIGITAÇÃO
  // ============================================
  
  /**
   * Configurações de digitação humanizada
   */
  TYPING: {
    /**
     * Se a digitação humanizada está habilitada
     * @type {boolean}
     */
    ENABLED: true,
    
    /**
     * Delay mínimo entre caracteres (ms)
     * @type {number}
     */
    MIN_DELAY: 50,
    
    /**
     * Delay máximo entre caracteres (ms)
     * @type {number}
     */
    MAX_DELAY: 150,
    
    /**
     * Chance de fazer uma pausa maior durante digitação (0-1)
     * Simula quando humanos param para pensar
     * @type {number}
     */
    PAUSE_CHANCE: 0.05,
    
    /**
     * Duração da pausa durante digitação (ms)
     * @type {Object}
     */
    PAUSE_DURATION: {
      MIN: 300,
      MAX: 800
    },
    
    /**
     * Chance de cometer um erro de digitação e corrigir (0-1)
     * @type {number}
     */
    TYPO_CHANCE: 0.02,
    
    /**
     * Delay antes de corrigir erro de digitação (ms)
     * @type {Object}
     */
    TYPO_CORRECTION_DELAY: {
      MIN: 200,
      MAX: 500
    },
    
    /**
     * Variação de velocidade por tipo de caractere
     * Números são digitados mais devagar que letras
     */
    CHAR_SPEED_VARIATION: {
      LETTERS: 1.0,      // Velocidade normal
      NUMBERS: 1.3,      // 30% mais lento
      SPECIAL: 1.5,      // 50% mais lento (símbolos)
      SPACE: 0.8         // 20% mais rápido
    }
  },
  
  // ============================================
  // CONFIGURAÇÕES DE MOUSE
  // ============================================
  
  /**
   * Configurações de movimento do mouse
   */
  MOUSE: {
    /**
     * Se o movimento humanizado do mouse está habilitado
     * @type {boolean}
     */
    ENABLED: true,
    
    /**
     * Velocidade do movimento do mouse (pixels por step)
     * @type {Object}
     */
    SPEED: {
      MIN: 5,
      MAX: 15
    },
    
    /**
     * Número de passos para mover o mouse até o destino
     * Mais passos = movimento mais suave
     * @type {Object}
     */
    STEPS: {
      MIN: 10,
      MAX: 25
    },
    
    /**
     * Curvatura do movimento (0 = linha reta, 1 = muito curvo)
     * @type {number}
     */
    CURVE_INTENSITY: 0.3,
    
    /**
     * Chance de fazer um pequeno movimento aleatório antes de clicar (0-1)
     * @type {number}
     */
    JITTER_CHANCE: 0.1,
    
    /**
     * Intensidade do jitter em pixels
     * @type {Object}
     */
    JITTER_INTENSITY: {
      MIN: 2,
      MAX: 8
    },
    
    /**
     * Delay antes de clicar após mover o mouse (ms)
     * @type {Object}
     */
    PRE_CLICK_DELAY: {
      MIN: 100,
      MAX: 300
    },
    
    /**
     * Delay após clicar (ms)
     * @type {Object}
     */
    POST_CLICK_DELAY: {
      MIN: 200,
      MAX: 500
    }
  },
  
  // ============================================
  // CONFIGURAÇÕES DE SCROLL
  // ============================================
  
  /**
   * Configurações de scroll humanizado
   */
  SCROLL: {
    /**
     * Se o scroll humanizado está habilitado
     * @type {boolean}
     */
    ENABLED: true,
    
    /**
     * Velocidade do scroll (pixels por step)
     * @type {Object}
     */
    SPEED: {
      MIN: 50,
      MAX: 150
    },
    
    /**
     * Delay entre steps de scroll (ms)
     * @type {Object}
     */
    STEP_DELAY: {
      MIN: 30,
      MAX: 80
    },
    
    /**
     * Chance de fazer uma pausa durante scroll (0-1)
     * @type {number}
     */
    PAUSE_CHANCE: 0.1,
    
    /**
     * Duração da pausa durante scroll (ms)
     * @type {Object}
     */
    PAUSE_DURATION: {
      MIN: 500,
      MAX: 1500
    }
  },
  
  // ============================================
  // CONFIGURAÇÕES DE PAUSAS
  // ============================================
  
  /**
   * Configurações de pausas aleatórias
   */
  PAUSES: {
    /**
     * Se as pausas aleatórias estão habilitadas
     * @type {boolean}
     */
    ENABLED: true,
    
    /**
     * Chance de fazer uma pausa entre ações (0-1)
     * @type {number}
     */
    CHANCE: 0.15,
    
    /**
     * Duração das pausas curtas (ms)
     * @type {Object}
     */
    SHORT: {
      MIN: 500,
      MAX: 1500
    },
    
    /**
     * Duração das pausas médias (ms)
     * @type {Object}
     */
    MEDIUM: {
      MIN: 2000,
      MAX: 5000
    },
    
    /**
     * Duração das pausas longas (ms)
     * @type {Object}
     */
    LONG: {
      MIN: 5000,
      MAX: 10000
    },
    
    /**
     * Chance de pausa longa (simula distração)
     * @type {number}
     */
    LONG_PAUSE_CHANCE: 0.02
  },
  
  // ============================================
  // CONFIGURAÇÕES ENTRE CONTAS
  // ============================================
  
  /**
   * Configurações de delay entre processamento de contas
   */
  BETWEEN_ACCOUNTS: {
    /**
     * Delay mínimo entre contas (ms)
     * @type {number}
     */
    MIN_DELAY: 5000,
    
    /**
     * Delay máximo entre contas (ms)
     * @type {number}
     */
    MAX_DELAY: 15000,
    
    /**
     * Chance de fazer uma pausa extra longa entre contas (0-1)
     * @type {number}
     */
    EXTRA_PAUSE_CHANCE: 0.1,
    
    /**
     * Duração da pausa extra (ms)
     * @type {Object}
     */
    EXTRA_PAUSE_DURATION: {
      MIN: 20000,
      MAX: 60000
    }
  },
  
  // ============================================
  // CONFIGURAÇÕES ENTRE CARTÕES
  // ============================================
  
  /**
   * Configurações de delay entre testes de cartões
   */
  BETWEEN_CARDS: {
    /**
     * Delay mínimo entre cartões (ms)
     * @type {number}
     */
    MIN_DELAY: 3000,
    
    /**
     * Delay máximo entre cartões (ms)
     * @type {number}
     */
    MAX_DELAY: 8000
  },
  
  // ============================================
  // CONFIGURAÇÕES DE CAMPOS
  // ============================================
  
  /**
   * Configurações de delay entre campos do formulário
   */
  BETWEEN_FIELDS: {
    /**
     * Delay mínimo entre campos (ms)
     * @type {number}
     */
    MIN_DELAY: 500,
    
    /**
     * Delay máximo entre campos (ms)
     * @type {number}
     */
    MAX_DELAY: 2000,
    
    /**
     * Chance de "revisar" o campo anterior (olhar para trás)
     * @type {number}
     */
    REVIEW_CHANCE: 0.05,
    
    /**
     * Delay da revisão (ms)
     * @type {Object}
     */
    REVIEW_DELAY: {
      MIN: 1000,
      MAX: 3000
    }
  },
  
  // ============================================
  // CONFIGURAÇÕES DE NAVEGAÇÃO
  // ============================================
  
  /**
   * Configurações de navegação entre páginas
   */
  NAVIGATION: {
    /**
     * Delay após carregar página (ms)
     * @type {Object}
     */
    AFTER_LOAD: {
      MIN: 2000,
      MAX: 5000
    },
    
    /**
     * Delay antes de interagir com a página (ms)
     * @type {Object}
     */
    BEFORE_INTERACT: {
      MIN: 1000,
      MAX: 3000
    },
    
    /**
     * Chance de fazer scroll exploratório após carregar página
     * @type {number}
     */
    EXPLORE_SCROLL_CHANCE: 0.2,
    
    /**
     * Quantidade de scroll exploratório (pixels)
     * @type {Object}
     */
    EXPLORE_SCROLL_AMOUNT: {
      MIN: 100,
      MAX: 400
    }
  }
};

// ============================================
// PRESETS DE HUMANIZAÇÃO
// ============================================

/**
 * Presets pré-configurados para diferentes níveis de humanização
 */
export const HUMANIZATION_PRESETS = {
  /**
   * Preset mínimo - Mais rápido, menos seguro
   */
  MINIMAL: {
    LEVEL: 1,
    TYPING: {
      MIN_DELAY: 20,
      MAX_DELAY: 50,
      PAUSE_CHANCE: 0.01,
      TYPO_CHANCE: 0
    },
    MOUSE: {
      STEPS: { MIN: 5, MAX: 10 },
      PRE_CLICK_DELAY: { MIN: 50, MAX: 100 }
    },
    PAUSES: {
      CHANCE: 0.05
    },
    BETWEEN_ACCOUNTS: {
      MIN_DELAY: 2000,
      MAX_DELAY: 5000
    }
  },
  
  /**
   * Preset balanceado - Recomendado para uso normal
   */
  BALANCED: {
    LEVEL: 3,
    TYPING: {
      MIN_DELAY: 50,
      MAX_DELAY: 150,
      PAUSE_CHANCE: 0.05,
      TYPO_CHANCE: 0.02
    },
    MOUSE: {
      STEPS: { MIN: 10, MAX: 25 },
      PRE_CLICK_DELAY: { MIN: 100, MAX: 300 }
    },
    PAUSES: {
      CHANCE: 0.15
    },
    BETWEEN_ACCOUNTS: {
      MIN_DELAY: 5000,
      MAX_DELAY: 15000
    }
  },
  
  /**
   * Preset seguro - Mais lento, mais seguro
   */
  SAFE: {
    LEVEL: 4,
    TYPING: {
      MIN_DELAY: 80,
      MAX_DELAY: 200,
      PAUSE_CHANCE: 0.1,
      TYPO_CHANCE: 0.03
    },
    MOUSE: {
      STEPS: { MIN: 15, MAX: 35 },
      PRE_CLICK_DELAY: { MIN: 200, MAX: 500 }
    },
    PAUSES: {
      CHANCE: 0.25
    },
    BETWEEN_ACCOUNTS: {
      MIN_DELAY: 10000,
      MAX_DELAY: 30000
    }
  },
  
  /**
   * Preset ultra seguro - Muito lento, máxima segurança
   */
  ULTRA_SAFE: {
    LEVEL: 5,
    TYPING: {
      MIN_DELAY: 100,
      MAX_DELAY: 300,
      PAUSE_CHANCE: 0.15,
      TYPO_CHANCE: 0.05
    },
    MOUSE: {
      STEPS: { MIN: 20, MAX: 50 },
      PRE_CLICK_DELAY: { MIN: 300, MAX: 700 }
    },
    PAUSES: {
      CHANCE: 0.35
    },
    BETWEEN_ACCOUNTS: {
      MIN_DELAY: 20000,
      MAX_DELAY: 60000
    }
  }
};

// ============================================
// FUNÇÕES UTILITÁRIAS
// ============================================

/**
 * Retorna um delay aleatório entre min e max
 * @param {number} min - Valor mínimo
 * @param {number} max - Valor máximo
 * @returns {number} - Delay aleatório
 */
export function getRandomDelay(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Retorna um delay de digitação baseado no caractere
 * @param {string} char - Caractere sendo digitado
 * @returns {number} - Delay em ms
 */
export function getTypingDelay(char) {
  if (!HUMANIZATION.TYPING.ENABLED) {
    return 30; // Delay mínimo se desabilitado
  }
  
  const baseDelay = getRandomDelay(
    HUMANIZATION.TYPING.MIN_DELAY,
    HUMANIZATION.TYPING.MAX_DELAY
  );
  
  // Aplicar variação baseada no tipo de caractere
  let multiplier = 1.0;
  
  if (/[a-zA-Z]/.test(char)) {
    multiplier = HUMANIZATION.TYPING.CHAR_SPEED_VARIATION.LETTERS;
  } else if (/[0-9]/.test(char)) {
    multiplier = HUMANIZATION.TYPING.CHAR_SPEED_VARIATION.NUMBERS;
  } else if (char === ' ') {
    multiplier = HUMANIZATION.TYPING.CHAR_SPEED_VARIATION.SPACE;
  } else {
    multiplier = HUMANIZATION.TYPING.CHAR_SPEED_VARIATION.SPECIAL;
  }
  
  return Math.floor(baseDelay * multiplier);
}

/**
 * Verifica se deve fazer uma pausa durante digitação
 * @returns {boolean}
 */
export function shouldTypingPause() {
  return HUMANIZATION.TYPING.ENABLED && 
         Math.random() < HUMANIZATION.TYPING.PAUSE_CHANCE;
}

/**
 * Retorna duração da pausa de digitação
 * @returns {number} - Duração em ms
 */
export function getTypingPauseDuration() {
  return getRandomDelay(
    HUMANIZATION.TYPING.PAUSE_DURATION.MIN,
    HUMANIZATION.TYPING.PAUSE_DURATION.MAX
  );
}

/**
 * Verifica se deve cometer um erro de digitação
 * @returns {boolean}
 */
export function shouldMakeTypo() {
  return HUMANIZATION.TYPING.ENABLED && 
         Math.random() < HUMANIZATION.TYPING.TYPO_CHANCE;
}

/**
 * Verifica se deve fazer uma pausa aleatória
 * @returns {boolean}
 */
export function shouldTakePause() {
  return HUMANIZATION.PAUSES.ENABLED && 
         Math.random() < HUMANIZATION.PAUSES.CHANCE;
}

/**
 * Retorna duração de uma pausa aleatória
 * @param {string} type - Tipo de pausa: 'short', 'medium', 'long'
 * @returns {number} - Duração em ms
 */
export function getPauseDuration(type = 'short') {
  const config = HUMANIZATION.PAUSES[type.toUpperCase()] || HUMANIZATION.PAUSES.SHORT;
  return getRandomDelay(config.MIN, config.MAX);
}

/**
 * Retorna delay entre contas
 * @returns {number} - Delay em ms
 */
export function getDelayBetweenAccounts() {
  let delay = getRandomDelay(
    HUMANIZATION.BETWEEN_ACCOUNTS.MIN_DELAY,
    HUMANIZATION.BETWEEN_ACCOUNTS.MAX_DELAY
  );
  
  // Chance de pausa extra longa
  if (Math.random() < HUMANIZATION.BETWEEN_ACCOUNTS.EXTRA_PAUSE_CHANCE) {
    delay += getRandomDelay(
      HUMANIZATION.BETWEEN_ACCOUNTS.EXTRA_PAUSE_DURATION.MIN,
      HUMANIZATION.BETWEEN_ACCOUNTS.EXTRA_PAUSE_DURATION.MAX
    );
  }
  
  return delay;
}

/**
 * Retorna delay entre cartões
 * @returns {number} - Delay em ms
 */
export function getDelayBetweenCards() {
  return getRandomDelay(
    HUMANIZATION.BETWEEN_CARDS.MIN_DELAY,
    HUMANIZATION.BETWEEN_CARDS.MAX_DELAY
  );
}

/**
 * Retorna delay entre campos
 * @returns {number} - Delay em ms
 */
export function getDelayBetweenFields() {
  return getRandomDelay(
    HUMANIZATION.BETWEEN_FIELDS.MIN_DELAY,
    HUMANIZATION.BETWEEN_FIELDS.MAX_DELAY
  );
}

/**
 * Aplica um preset de humanização
 * @param {string} presetName - Nome do preset: 'MINIMAL', 'BALANCED', 'SAFE', 'ULTRA_SAFE'
 */
export function applyPreset(presetName) {
  const preset = HUMANIZATION_PRESETS[presetName.toUpperCase()];
  if (!preset) {
    console.warn(`Preset '${presetName}' não encontrado. Usando BALANCED.`);
    return applyPreset('BALANCED');
  }
  
  // Aplicar valores do preset
  HUMANIZATION.LEVEL = preset.LEVEL;
  
  if (preset.TYPING) {
    Object.assign(HUMANIZATION.TYPING, preset.TYPING);
  }
  if (preset.MOUSE) {
    Object.assign(HUMANIZATION.MOUSE, preset.MOUSE);
  }
  if (preset.PAUSES) {
    Object.assign(HUMANIZATION.PAUSES, preset.PAUSES);
  }
  if (preset.BETWEEN_ACCOUNTS) {
    Object.assign(HUMANIZATION.BETWEEN_ACCOUNTS, preset.BETWEEN_ACCOUNTS);
  }
  
  console.log(`[Humanization] Preset '${presetName}' aplicado (Level ${preset.LEVEL})`);
}

/**
 * Retorna configuração atual de humanização
 * @returns {Object}
 */
export function getHumanizationConfig() {
  return { ...HUMANIZATION };
}

/**
 * Atualiza configuração de humanização
 * @param {Object} config - Novas configurações
 */
export function updateHumanizationConfig(config) {
  if (config.TYPING) {
    Object.assign(HUMANIZATION.TYPING, config.TYPING);
  }
  if (config.MOUSE) {
    Object.assign(HUMANIZATION.MOUSE, config.MOUSE);
  }
  if (config.PAUSES) {
    Object.assign(HUMANIZATION.PAUSES, config.PAUSES);
  }
  if (config.BETWEEN_ACCOUNTS) {
    Object.assign(HUMANIZATION.BETWEEN_ACCOUNTS, config.BETWEEN_ACCOUNTS);
  }
  if (config.BETWEEN_CARDS) {
    Object.assign(HUMANIZATION.BETWEEN_CARDS, config.BETWEEN_CARDS);
  }
  if (config.BETWEEN_FIELDS) {
    Object.assign(HUMANIZATION.BETWEEN_FIELDS, config.BETWEEN_FIELDS);
  }
  if (config.LEVEL !== undefined) {
    HUMANIZATION.LEVEL = config.LEVEL;
  }
  if (config.ENABLED !== undefined) {
    HUMANIZATION.ENABLED = config.ENABLED;
  }
}

export default HUMANIZATION;
