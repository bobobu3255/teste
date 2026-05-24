#!/usr/bin/env python3
"""
Gerador de Cartões de Crédito com Algoritmo de Luhn
Versão 2.1 - Corrigido para geração em massa (até 10000 cartões)
"""
import random
from typing import List, Set, Tuple, Optional, Callable
from datetime import datetime


class CardGenerator:
    """Gerador de cartões de crédito válidos usando algoritmo de Luhn - Otimizado"""
    
    def __init__(self):
        self.history: Set[str] = set()  # Histórico para evitar duplicatas
        self._cancelled = False  # Flag para cancelamento
    
    def cancel(self):
        """Cancela a geração em andamento"""
        self._cancelled = True
    
    def reset_cancel(self):
        """Reseta o flag de cancelamento"""
        self._cancelled = False
    
    def luhn_checksum(self, card_number: str) -> int:
        """
        Calcula o checksum de Luhn para um número de cartão
        
        Args:
            card_number: Número do cartão (sem o dígito verificador)
        
        Returns:
            Dígito verificador (0-9)
        """
        if not card_number.isdigit():
            return 0

        digits = [int(d) for d in f"{card_number}0"]
        total = 0
        for index, digit in enumerate(reversed(digits)):
            if index % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit

        return (10 - (total % 10)) % 10
    
    def validate_luhn(self, card_number: str) -> bool:
        """
        Valida se um número de cartão é válido segundo Luhn
        
        Args:
            card_number: Número completo do cartão
        
        Returns:
            True se válido, False caso contrário
        """
        if not card_number.isdigit():
            return False
        
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        total = sum(odd_digits)
        for d in even_digits:
            d = d * 2
            if d > 9:
                d = d - 9
            total += d
        
        return total % 10 == 0
    
    def _calculate_max_combinations(self, x_count: int, last_is_x: bool) -> int:
        """
        Calcula o número máximo de combinações possíveis
        
        Args:
            x_count: Quantidade de X no padrão
            last_is_x: Se o último dígito é X
        
        Returns:
            Número máximo de combinações únicas
        """
        # Se o último é X, ele é calculado pelo Luhn, então não conta
        variable_digits = x_count - 1 if last_is_x else x_count
        return 10 ** variable_digits if variable_digits > 0 else 1
    
    def generate_card(self, pattern: str) -> Optional[str]:
        """
        Gera um número de cartão válido baseado no padrão
        
        Args:
            pattern: Padrão com X para dígitos aleatórios (ex: 406669994713XXXX)
        
        Returns:
            Número de cartão válido ou None se não conseguir
        """
        # Remover espaços e converter para maiúsculo
        pattern = pattern.upper().replace(' ', '').replace('-', '')
        
        # Verificar se o padrão é válido
        if not all(c.isdigit() or c == 'X' for c in pattern):
            return None
        
        # Contar quantos X existem
        x_count = pattern.count('X')
        
        if x_count == 0:
            # Sem X, apenas validar
            return pattern if self.validate_luhn(pattern) else None
        
        # Se o último dígito é X, precisamos calcular o Luhn
        last_is_x = pattern[-1] == 'X'
        
        # Encontrar posições dos X
        x_positions = [i for i, c in enumerate(pattern) if c == 'X']
        
        # Gerar combinações até encontrar uma válida
        max_attempts = 1000
        for _ in range(max_attempts):
            # Substituir X por dígitos aleatórios
            card = list(pattern)
            
            for i in x_positions:
                # Se é o último dígito, deixar para calcular depois
                if i == len(card) - 1 and last_is_x:
                    continue
                card[i] = str(random.randint(0, 9))
            
            # Se o último é X, calcular o dígito verificador
            if last_is_x:
                partial = ''.join(card[:-1])
                checksum = self.luhn_checksum(partial)
                card[-1] = str(checksum)
            
            card_number = ''.join(card)
            
            # Verificar se é válido e não é duplicata
            if self.validate_luhn(card_number) and card_number not in self.history:
                return card_number
        
        return None
    
    def generate_card_fast(self, pattern: str, x_positions: List[int], 
                           last_is_x: bool) -> Optional[str]:
        """
        Versão otimizada para geração em massa - evita recálculos
        
        Args:
            pattern: Padrão já processado (maiúsculo, sem espaços)
            x_positions: Lista de posições dos X
            last_is_x: Se o último dígito é X
        
        Returns:
            Número de cartão válido ou None
        """
        card = list(pattern)
        
        # Substituir X por dígitos aleatórios
        for i in x_positions:
            if i == len(card) - 1 and last_is_x:
                continue
            card[i] = str(random.randint(0, 9))
        
        # Se o último é X, calcular o dígito verificador
        if last_is_x:
            partial = ''.join(card[:-1])
            checksum = self.luhn_checksum(partial)
            card[-1] = str(checksum)
        
        card_number = ''.join(card)
        
        # Verificar se é válido e não é duplicata
        if self.validate_luhn(card_number) and card_number not in self.history:
            return card_number
        
        return None
    
    def generate_cards(self, pattern: str, quantity: int, 
                       month: str, year: str, cvv: str,
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> List[str]:
        """
        Gera múltiplos cartões com formatação completa - OTIMIZADO v2.1
        
        Args:
            pattern: Padrão do cartão
            quantity: Quantidade a gerar
            month: Mês de expiração (01-12)
            year: Ano de expiração (2 ou 4 dígitos)
            cvv: CVV (3-4 dígitos)
            progress_callback: Função callback(atual, total) para reportar progresso
        
        Returns:
            Lista de cartões no formato NUMERO|MES|ANO|CVV
        """
        self._cancelled = False
        cards = []
        attempts = 0
        
        # Normalizar ano para 2 dígitos se necessário
        if len(year) == 4:
            year = year[-2:]
        
        # Verificar se CVV é aleatório
        cvv_is_random = str(cvv).upper() == "RANDOM"
        
        # Pré-processar padrão para otimização
        pattern_clean = pattern.upper().replace(' ', '').replace('-', '')
        x_positions = [i for i, c in enumerate(pattern_clean) if c == 'X']
        last_is_x = pattern_clean[-1] == 'X' if pattern_clean else False
        has_x = len(x_positions) > 0
        x_count = len(x_positions)
        
        # Calcular máximo de combinações possíveis
        max_combinations = self._calculate_max_combinations(x_count, last_is_x)
        
        # Calcular limite de tentativas de forma mais inteligente
        # Para padrões com poucos X, aumentar o multiplicador
        if x_count <= 2:
            # Poucos X = poucas combinações, aumentar tentativas
            max_attempts = min(max_combinations * 10, quantity * 500)
        elif x_count <= 4:
            max_attempts = quantity * 200
        else:
            # Muitos X = muitas combinações, limite normal
            max_attempts = quantity * 100
        
        # Garantir um mínimo de tentativas
        max_attempts = max(max_attempts, quantity * 50)
        
        # Verificar se é possível gerar a quantidade solicitada
        # Considerando o histórico existente
        available_combinations = max_combinations - len(self.history)
        if available_combinations < quantity and x_count > 0:
            # Ajustar expectativa mas continuar tentando
            pass
        
        # Calcular intervalo de atualização de progresso
        # Para quantidades pequenas, atualizar a cada 1
        # Para quantidades grandes, atualizar a cada 1%
        if quantity <= 100:
            progress_interval = 1
        else:
            progress_interval = max(1, quantity // 100)
        
        while len(cards) < quantity and attempts < max_attempts:
            # Verificar cancelamento
            if self._cancelled:
                break
            
            # Gerar cartão usando método otimizado
            if has_x:
                card_number = self.generate_card_fast(pattern_clean, x_positions, last_is_x)
            else:
                # Sem X, só pode gerar 1 cartão
                if len(cards) == 0:
                    card_number = pattern_clean if self.validate_luhn(pattern_clean) else None
                else:
                    break  # Não pode gerar mais sem X
            
            if card_number and card_number not in self.history:
                self.history.add(card_number)
                # Gerar CVV aleatório se necessário
                if cvv_is_random:
                    current_cvv = f"{random.randint(0, 999):03d}"
                else:
                    current_cvv = cvv
                formatted = f"{card_number}|{month}|{year}|{current_cvv}"
                cards.append(formatted)
                
                # Reportar progresso
                if progress_callback and len(cards) % progress_interval == 0:
                    progress_callback(len(cards), quantity)
            
            attempts += 1
            
            # O historico e global; nao deve limitar um novo padrao diferente.
        
        # Reportar progresso final
        if progress_callback:
            progress_callback(len(cards), quantity)
        
        return cards
    
    def clear_history(self):
        """Limpa o histórico de cartões gerados"""
        self.history.clear()
    
    def get_history_count(self) -> int:
        """Retorna quantidade de cartões no histórico"""
        return len(self.history)


# Teste rápido
if __name__ == '__main__':
    gen = CardGenerator()
    
    def show_progress(current, total):
        percent = (current / total) * 100
        print(f"\rProgresso: {current}/{total} ({percent:.1f}%)", end='', flush=True)
    
    # Testar geração de 1000 cartões
    pattern = "406669994713XXXX"
    print(f"Gerando 1000 cartões com padrão: {pattern}")
    cards = gen.generate_cards(pattern, 1000, "10", "2031", "000", show_progress)
    
    print(f"\n\nGerados: {len(cards)} cartões")
    print("-" * 40)
    for card in cards[:10]:  # Mostrar apenas os 10 primeiros
        print(card)
    print("...")
    
    # Validar todos
    print("-" * 40)
    valid_count = sum(1 for card in cards if gen.validate_luhn(card.split('|')[0]))
    print(f"Válidos: {valid_count}/{len(cards)}")
