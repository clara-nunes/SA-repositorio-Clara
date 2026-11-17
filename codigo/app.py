"""
Sistema de Delivery de Comida - Funcionalidade inicial: realização de pedidos.

Objetivo:
    Permitir que um cliente monte um pedido a partir de um cardápio, aplicando
    regras de negócio claras e validando todas as entradas antes de aceitá-las.

Organização do arquivo (de cima para baixo):
    1. Constantes de regras de negócio
    2. Exceções personalizadas
    3. Funções de validação e formatação
    4. Modelos de dados (Cliente, ItemCardapio, ItemPedido)
    5. Regras do pedido (classe Pedido)
    6. Serviços (Cardapio e PedidoServico)
    7. Demonstração (função principal)

Cuidados éticos (CS1 a CS3):
    - Transparência: o cliente sempre vê subtotal, taxa de entrega, desconto e total.
    - Privacidade (LGPD): coletamos apenas os dados necessários e mascaramos o
      telefone ao exibi-lo.
    - Honestidade: nenhum valor é alterado em silêncio; toda recusa informa o motivo.

Como executar:
    python delivery.py
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import re

# =============================================================================
# 1. CONSTANTES DE REGRAS DE NEGÓCIO
# =============================================================================
# Manter as regras em um só lugar facilita a manutenção: para mudar uma regra,
# basta alterar o valor aqui, sem mexer na lógica do restante do código.

PEDIDO_MINIMO = Decimal("15.00")        # Subtotal mínimo para confirmar o pedido.
QUANTIDADE_MAXIMA_POR_ITEM = 20         # Limite para evitar erros de digitação.
DISTANCIA_MAXIMA_KM = Decimal("10")     # Acima disso, não realizamos entregas.
FRETE_GRATIS_A_PARTIR_DE = Decimal("100.00")

# Faixas de entrega: (distância máxima em km, valor da taxa).
FAIXAS_DE_ENTREGA = [
    (Decimal("3"), Decimal("5.00")),
    (Decimal("7"), Decimal("8.00")),
    (Decimal("10"), Decimal("12.00")),
]

# Cupons disponíveis: código do cupom e percentual de desconto sobre o subtotal.
CUPONS = {
    "PRIMEIRA10": Decimal("0.10"),
    "FESTA15": Decimal("0.15"),
}

CENTAVOS = Decimal("0.01")  # Usado para arredondar valores em dinheiro.


# =============================================================================
# 2. EXCEÇÕES PERSONALIZADAS
# =============================================================================
# Separar os erros em dois tipos deixa claro o que aconteceu:
# dado inválido digitado pelo usuário ou regra de negócio não atendida.

class ErroDeValidacao(Exception):
    """Erro lançado quando um dado informado é inválido."""


class ErroDeNegocio(Exception):
    """Erro lançado quando uma regra de negócio não é atendida."""


# =============================================================================
# 3. FUNÇÕES DE VALIDAÇÃO E FORMATAÇÃO
# =============================================================================

def converter_para_dinheiro(valor, campo="valor"):
    """Converte um valor para Decimal com duas casas e garante que seja positivo."""
    try:
        # Usamos str() para evitar imprecisões de números float (ex.: 0.1 + 0.2).
        numero = Decimal(str(valor).replace(",", ".").strip())
    except Exception:
        raise ErroDeValidacao(f"O campo '{campo}' deve ser um número válido.")
    if not numero.is_finite() or numero <= 0:
        raise ErroDeValidacao(f"O campo '{campo}' deve ser maior que zero.")
    return numero.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def validar_nome(nome):
    """Valida o nome: mínimo de 3 letras, aceitando acentos, espaços, hífen e apóstrofo."""
    nome = str(nome).strip()
    if len(nome) < 3:
        raise ErroDeValidacao("O nome deve ter pelo menos 3 caracteres.")
    # O padrão abaixo aceita letras (inclusive acentuadas), espaço, hífen e apóstrofo.
    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ' -]+", nome):
        raise ErroDeValidacao("O nome deve conter apenas letras e espaços.")
    return nome


def validar_telefone(telefone):
    """Valida o telefone brasileiro com DDD (10 ou 11 dígitos) e retorna só os números."""
    apenas_digitos = re.sub(r"\D", "", str(telefone))  # Remove tudo que não é dígito.
    if len(apenas_digitos) not in (10, 11):
        raise ErroDeValidacao("O telefone deve ter DDD e 8 ou 9 dígitos.")
    return apenas_digitos


def validar_endereco(endereco):
    """Valida o endereço: precisa ter um mínimo de informação para a entrega."""
    endereco = str(endereco).strip()
    if len(endereco) < 8:
        raise ErroDeValidacao("O endereço está muito curto. Informe rua, número e bairro.")
    return endereco


def validar_quantidade(quantidade):
    """Valida a quantidade de um item: inteiro entre 1 e o limite máximo."""
    try:
        numero = int(quantidade)
    except (TypeError, ValueError):
        raise ErroDeValidacao("A quantidade deve ser um número inteiro.")
    if numero != quantidade and not isinstance(quantidade, str):
        raise ErroDeValidacao("A quantidade deve ser um número inteiro.")
    if not 1 <= numero <= QUANTIDADE_MAXIMA_POR_ITEM:
        raise ErroDeValidacao(
            f"A quantidade deve estar entre 1 e {QUANTIDADE_MAXIMA_POR_ITEM}."
        )
    return numero


def validar_distancia(distancia_km):
    """Valida a distância de entrega: maior que zero e dentro da área de atendimento."""
    distancia = converter_para_dinheiro(distancia_km, "distância")
    if distancia > DISTANCIA_MAXIMA_KM:
        raise ErroDeNegocio(
            f"Não entregamos a mais de {DISTANCIA_MAXIMA_KM} km de distância."
        )
    return distancia


def formatar_moeda(valor):
    """Formata um Decimal no padrão brasileiro. Exemplo: 1234.5 vira 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"  # Exemplo: '1,234.50' (padrão americano).
    # Trocamos os separadores usando um caractere temporário.
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"


# =============================================================================
# 4. MODELOS DE DADOS
# =============================================================================

@dataclass(frozen=True)  # frozen=True deixa o objeto imutável após criado.
class Cliente:
    """Representa o cliente. Os dados são validados no momento da criação."""

    nome: str
    telefone: str
    endereco: str

    def __post_init__(self):
        # Método especial chamado logo após a criação do objeto.
        # Como o objeto é imutável, usamos object.__setattr__ para gravar os valores limpos.
        object.__setattr__(self, "nome", validar_nome(self.nome))
        object.__setattr__(self, "telefone", validar_telefone(self.telefone))
        object.__setattr__(self, "endereco", validar_endereco(self.endereco))

    def telefone_mascarado(self):
        """Exibe o telefone sem revelar todos os dígitos (proteção de dados, LGPD)."""
        return f"({self.telefone[:2]}) *****-{self.telefone[-4:]}"


@dataclass(frozen=True)
class ItemCardapio:
    """Representa um produto vendido pelo restaurante."""

    codigo: str
    nome: str
    preco: Decimal

    def __post_init__(self):
        if not str(self.codigo).strip():
            raise ErroDeValidacao("O código do item não pode ser vazio.")
        if not str(self.nome).strip():
            raise ErroDeValidacao("O nome do item não pode ser vazio.")
        object.__setattr__(self, "preco", converter_para_dinheiro(self.preco, "preço"))


@dataclass(frozen=True)
class ItemPedido:
    """Representa um item do cardápio com a quantidade escolhida pelo cliente."""

    item: ItemCardapio
    quantidade: int

    @property  # Permite usar item_pedido.subtotal como se fosse um atributo.
    def subtotal(self):
        return self.item.preco * self.quantidade


class StatusPedido(Enum):
    """Etapas possíveis na vida de um pedido."""

    RASCUNHO = "Rascunho"
    CONFIRMADO = "Confirmado"
    EM_PREPARO = "Em preparo"
    SAIU_PARA_ENTREGA = "Saiu para entrega"
    ENTREGUE = "Entregue"
    CANCELADO = "Cancelado"


# Define quais mudanças de status são permitidas (evita saltos ilógicos).
TRANSICOES_PERMITIDAS = {
    StatusPedido.RASCUNHO: {StatusPedido.CONFIRMADO, StatusPedido.CANCELADO},
    StatusPedido.CONFIRMADO: {StatusPedido.EM_PREPARO, StatusPedido.CANCELADO},
    StatusPedido.EM_PREPARO: {StatusPedido.SAIU_PARA_ENTREGA, StatusPedido.CANCELADO},
    StatusPedido.SAIU_PARA_ENTREGA: {StatusPedido.ENTREGUE},
    StatusPedido.ENTREGUE: set(),
    StatusPedido.CANCELADO: set(),
}


# =============================================================================
# 5. REGRAS DO PEDIDO
# =============================================================================

class Pedido:
    """Concentra as regras de cálculo e de status de um pedido."""

    def __init__(self, numero, cliente, distancia_km):
        self.numero = numero
        self.cliente = cliente
        self.distancia_km = validar_distancia(distancia_km)
        self.status = StatusPedido.RASCUNHO
        self._itens = []        # Lista interna de ItemPedido (o "_" indica uso interno).
        self._cupom = None      # Código do cupom aplicado, se houver.

    # ---------- Itens e cupom ----------

    def adicionar_item(self, item, quantidade):
        """Adiciona um item ao pedido. Só é permitido enquanto o pedido é rascunho."""
        self._exigir_rascunho()
        quantidade = validar_quantidade(quantidade)

        # Se o item já existe no pedido, somamos as quantidades em vez de duplicar a linha.
        for posicao, existente in enumerate(self._itens):
            if existente.item.codigo == item.codigo:
                nova_quantidade = existente.quantidade + quantidade
                validar_quantidade(nova_quantidade)  # Garante que o total respeita o limite.
                self._itens[posicao] = ItemPedido(item, nova_quantidade)
                return
        self._itens.append(ItemPedido(item, quantidade))

    def aplicar_cupom(self, codigo):
        """Aplica um cupom de desconto, caso o código seja válido."""
        self._exigir_rascunho()
        codigo = str(codigo).strip().upper()
        if codigo not in CUPONS:
            raise ErroDeNegocio(f"O cupom '{codigo}' é inválido ou expirou.")
        self._cupom = codigo

    # ---------- Cálculos ----------

    @property
    def itens(self):
        return tuple(self._itens)  # Tupla impede alterações externas na lista.

    @property
    def subtotal(self):
        return sum((i.subtotal for i in self._itens), Decimal("0.00"))

    @property
    def desconto(self):
        if self._cupom is None:
            return Decimal("0.00")
        return (self.subtotal * CUPONS[self._cupom]).quantize(CENTAVOS, ROUND_HALF_UP)

    @property
    def taxa_entrega(self):
        if self.subtotal >= FRETE_GRATIS_A_PARTIR_DE:
            return Decimal("0.00")
        for limite_km, taxa in FAIXAS_DE_ENTREGA:
            if self.distancia_km <= limite_km:
                return taxa
        # Esta linha só é alcançada se as faixas e o limite máximo estiverem inconsistentes.
        raise ErroDeNegocio("Não há faixa de entrega para esta distância.")

    @property
    def total(self):
        return self.subtotal - self.desconto + self.taxa_entrega

    # ---------- Status ----------

    def confirmar(self):
        """Confirma o pedido após verificar as regras obrigatórias."""
        if not self._itens:
            raise ErroDeNegocio("O pedido precisa ter pelo menos um item.")
        if self.subtotal < PEDIDO_MINIMO:
            raise ErroDeNegocio(
                f"O pedido mínimo é de {formatar_moeda(PEDIDO_MINIMO)}. "
                f"Faltam {formatar_moeda(PEDIDO_MINIMO - self.subtotal)}."
            )
        self._mudar_status(StatusPedido.CONFIRMADO)

    def avancar(self, novo_status):
        """Avança o pedido para a próxima etapa, respeitando as transições permitidas."""
        self._mudar_status(novo_status)

    def cancelar(self):
        """Cancela o pedido. Não é possível cancelar após a saída para entrega."""
        self._mudar_status(StatusPedido.CANCELADO)

    # ---------- Apoio interno ----------

    def _mudar_status(self, novo_status):
        if novo_status not in TRANSICOES_PERMITIDAS[self.status]:
            raise ErroDeNegocio(
                f"Não é possível mudar de '{self.status.value}' para '{novo_status.value}'."
            )
        self.status = novo_status

    def _exigir_rascunho(self):
        if self.status != StatusPedido.RASCUNHO:
            raise ErroDeNegocio("O pedido não pode mais ser alterado após a confirmação.")

    def resumo(self):
        """Gera um texto com todos os valores detalhados (transparência com o cliente)."""
        linhas = [
            f"Pedido nº {self.numero} - {self.status.value}",
            f"Cliente: {self.cliente.nome} | Telefone: {self.cliente.telefone_mascarado()}",
            f"Endereço: {self.cliente.endereco} ({str(self.distancia_km).replace('.', ',')} km)",
            "Itens:",
        ]
        for i in self._itens:
            linhas.append(
                f"  {i.quantidade}x {i.item.nome} - {formatar_moeda(i.subtotal)}"
            )
        linhas.append(f"Subtotal:         {formatar_moeda(self.subtotal)}")
        if self._cupom:
            linhas.append(f"Desconto ({self._cupom}): -{formatar_moeda(self.desconto)}")
        linhas.append(f"Taxa de entrega:  {formatar_moeda(self.taxa_entrega)}")
        linhas.append(f"TOTAL:            {formatar_moeda(self.total)}")
        return "\n".join(linhas)


# =============================================================================
# 6. SERVIÇOS
# =============================================================================

class Cardapio:
    """Guarda os itens disponíveis e permite consultá-los pelo código."""

    def __init__(self):
        self._itens = {}  # Dicionário: código do item -> ItemCardapio.

    def adicionar(self, item):
        if item.codigo in self._itens:
            raise ErroDeNegocio(f"Já existe um item com o código '{item.codigo}'.")
        self._itens[item.codigo] = item

    def buscar(self, codigo):
        codigo = str(codigo).strip().upper()
        if codigo not in self._itens:
            raise ErroDeNegocio(f"O item '{codigo}' não existe no cardápio.")
        return self._itens[codigo]

    def listar(self):
        return list(self._itens.values())


class PedidoServico:
    """Cria e armazena pedidos, entregando a cada um um número sequencial."""

    def __init__(self, cardapio):
        self._cardapio = cardapio
        self._pedidos = {}
        self._proximo_numero = 1

    def criar_pedido(self, cliente, distancia_km):
        pedido = Pedido(self._proximo_numero, cliente, distancia_km)
        self._pedidos[pedido.numero] = pedido
        self._proximo_numero += 1
        return pedido

    def adicionar_item_por_codigo(self, pedido, codigo, quantidade):
        """Busca o item no cardápio pelo código e o adiciona ao pedido."""
        pedido.adicionar_item(self._cardapio.buscar(codigo), quantidade)


# =============================================================================
# 7. DEMONSTRAÇÃO
# =============================================================================

def executar_e_mostrar_erro(descricao, acao):
    """Executa uma ação e exibe a mensagem caso uma regra seja violada."""
    try:
        acao()
        print(f"[OK]   {descricao}")
    except (ErroDeValidacao, ErroDeNegocio) as erro:
        print(f"[ERRO] {descricao}: {erro}")


def principal():
    # --- Monta o cardápio do restaurante ---
    cardapio = Cardapio()
    cardapio.adicionar(ItemCardapio("HB01", "Hambúrguer Artesanal", "28.90"))
    cardapio.adicionar(ItemCardapio("PZ01", "Pizza Margherita", "45.00"))
    cardapio.adicionar(ItemCardapio("RF01", "Refrigerante Lata", "6.50"))
    cardapio.adicionar(ItemCardapio("SC01", "Suco Natural", "9.00"))

    print("=== CARDÁPIO ===")
    for item in cardapio.listar():
        print(f"{item.codigo} - {item.nome}: {formatar_moeda(item.preco)}")

    servico = PedidoServico(cardapio)

    # --- Cenário 1: fluxo completo e bem-sucedido ---
    print("\n=== CENÁRIO 1: PEDIDO COMPLETO ===")
    cliente = Cliente("Maria da Silva", "(51) 99876-5432", "Rua das Flores, 120, Centro")
    pedido = servico.criar_pedido(cliente, "4.5")
    servico.adicionar_item_por_codigo(pedido, "HB01", 2)
    servico.adicionar_item_por_codigo(pedido, "RF01", 2)
    pedido.aplicar_cupom("primeira10")  # O código é normalizado para maiúsculas.
    pedido.confirmar()
    pedido.avancar(StatusPedido.EM_PREPARO)
    print(pedido.resumo())

    # --- Cenário 2: frete grátis ---
    print("\n=== CENÁRIO 2: FRETE GRÁTIS ===")
    pedido2 = servico.criar_pedido(cliente, 2)
    servico.adicionar_item_por_codigo(pedido2, "PZ01", 3)
    pedido2.confirmar()
    print(pedido2.resumo())

    # --- Cenário 3: validações e regras sendo aplicadas ---
    print("\n=== CENÁRIO 3: ENTRADAS INVÁLIDAS E REGRAS DE NEGÓCIO ===")
    executar_e_mostrar_erro(
        "Cliente com nome inválido",
        lambda: Cliente("A1", "51998765432", "Rua das Flores, 120"),
    )
    executar_e_mostrar_erro(
        "Cliente com telefone inválido",
        lambda: Cliente("João Pereira", "12345", "Rua das Flores, 120"),
    )
    executar_e_mostrar_erro(
        "Entrega fora da área de atendimento",
        lambda: servico.criar_pedido(cliente, 25),
    )

    pedido3 = servico.criar_pedido(cliente, 5)
    executar_e_mostrar_erro(
        "Quantidade negativa",
        lambda: servico.adicionar_item_por_codigo(pedido3, "SC01", -1),
    )
    executar_e_mostrar_erro(
        "Quantidade acima do limite",
        lambda: servico.adicionar_item_por_codigo(pedido3, "SC01", 50),
    )
    executar_e_mostrar_erro(
        "Item inexistente no cardápio",
        lambda: servico.adicionar_item_por_codigo(pedido3, "XX99", 1),
    )
    executar_e_mostrar_erro(
        "Cupom inválido",
        lambda: pedido3.aplicar_cupom("DESCONTAO"),
    )
    servico.adicionar_item_por_codigo(pedido3, "SC01", 1)
    executar_e_mostrar_erro(
        "Confirmação abaixo do pedido mínimo",
        pedido3.confirmar,
    )
    executar_e_mostrar_erro(
        "Cancelamento de pedido que já saiu para entrega",
        lambda: (
            pedido.avancar(StatusPedido.SAIU_PARA_ENTREGA),
            pedido.cancelar(),
        ),
    )


if __name__ == "__main__":
    # Este bloco só executa quando o arquivo é rodado diretamente,
    # e não quando ele é importado por outro arquivo.
    principal()