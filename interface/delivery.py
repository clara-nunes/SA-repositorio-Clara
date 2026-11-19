"""
Sistema de Delivery de Comida - Funcionalidade inicial: realizacao de pedidos.

Objetivo:
    Permitir que um cliente monte um pedido a partir de um cardapio, aplicando
    regras de negocio claras e validando todas as entradas antes de aceita-las.

Organizacao do arquivo (de cima para baixo):
    1. Constantes de regras de negocio
    2. Excecoes personalizadas
    3. Funcoes de validacao e formatacao
    4. Modelos de dados (Cliente, ItemCardapio, ItemPedido)
    5. Regras do pedido (classe Pedido)
    6. Servicos (Cardapio e PedidoServico)
    7. Demonstracao (funcao principal)

Cuidados eticos (CS1 a CS3):
    - Transparencia: o cliente sempre ve subtotal, taxa de entrega, desconto e total.
    - Privacidade (LGPD): coletamos apenas os dados necessarios e mascaramos o
      telefone ao exibi-lo.
    - Honestidade: nenhum valor e alterado em silencio; toda recusa informa o motivo.

Como executar:
    python delivery.py
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import re

# =============================================================================
# 1. CONSTANTES DE REGRAS DE NEGOCIO
# =============================================================================
# Manter as regras em um so lugar facilita a manutencao: para mudar uma regra,
# basta alterar o valor aqui, sem mexer na logica do restante do codigo.

PEDIDO_MINIMO = Decimal("15.00")        # Subtotal minimo para confirmar o pedido.
QUANTIDADE_MAXIMA_POR_ITEM = 20         # Limite para evitar erros de digitacao.
DISTANCIA_MAXIMA_KM = Decimal("10")     # Acima disso, nao realizamos entregas.
FRETE_GRATIS_A_PARTIR_DE = Decimal("100.00")

# Faixas de entrega: (distancia maxima em km, valor da taxa).
FAIXAS_DE_ENTREGA = [
    (Decimal("3"), Decimal("5.00")),
    (Decimal("7"), Decimal("8.00")),
    (Decimal("10"), Decimal("12.00")),
]

# Cupons disponiveis: codigo do cupom e percentual de desconto sobre o subtotal.
CUPONS = {
    "PRIMEIRA10": Decimal("0.10"),
    "FESTA15": Decimal("0.15"),
}

CENTAVOS = Decimal("0.01")  # Usado para arredondar valores em dinheiro.


# =============================================================================
# 2. EXCECOES PERSONALIZADAS
# =============================================================================
# Separar os erros em dois tipos deixa claro o que aconteceu:
# dado invalido digitado pelo usuario ou regra de negocio nao atendida.

class ErroDeValidacao(Exception):
    """Erro lancado quando um dado informado e invalido."""


class ErroDeNegocio(Exception):
    """Erro lancado quando uma regra de negocio nao e atendida."""


# =============================================================================
# 3. FUNCOES DE VALIDACAO E FORMATACAO
# =============================================================================

def converter_para_dinheiro(valor, campo="valor"):
    """Converte um valor para Decimal com duas casas e garante que seja positivo."""
    try:
        # Usamos str() para evitar imprecisoes de numeros float (ex.: 0.1 + 0.2).
        numero = Decimal(str(valor).replace(",", ".").strip())
    except Exception:
        raise ErroDeValidacao(f"O campo '{campo}' deve ser um numero valido.")
    if not numero.is_finite() or numero <= 0:
        raise ErroDeValidacao(f"O campo '{campo}' deve ser maior que zero.")
    return numero.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def validar_nome(nome):
    """Valida o nome: minimo de 3 letras, aceitando acentos, espacos, hifen e apostrofo."""
    nome = str(nome).strip()
    if len(nome) < 3:
        raise ErroDeValidacao("O nome deve ter pelo menos 3 caracteres.")
    # Cada caractere deve ser letra, espaco, hifen ou apostrofo (isalpha aceita acentos).
    if not all(c.isalpha() or c in " '-" for c in nome):
        raise ErroDeValidacao("O nome deve conter apenas letras e espacos.")
    return nome


def validar_telefone(telefone):
    """Valida o telefone brasileiro com DDD (10 ou 11 digitos) e retorna so os numeros."""
    apenas_digitos = re.sub(r"\D", "", str(telefone))  # Remove tudo que nao e digito.
    if len(apenas_digitos) not in (10, 11):
        raise ErroDeValidacao("O telefone deve ter DDD e 8 ou 9 digitos.")
    return apenas_digitos


def validar_endereco(endereco):
    """Valida o endereco: precisa ter um minimo de informacao para a entrega."""
    endereco = str(endereco).strip()
    if len(endereco) < 8:
        raise ErroDeValidacao("O endereco esta muito curto. Informe rua, numero e bairro.")
    return endereco


def validar_quantidade(quantidade):
    """Valida a quantidade de um item: inteiro entre 1 e o limite maximo."""
    try:
        numero = int(quantidade)
    except (TypeError, ValueError):
        raise ErroDeValidacao("A quantidade deve ser um numero inteiro.")
    if numero != quantidade and not isinstance(quantidade, str):
        raise ErroDeValidacao("A quantidade deve ser um numero inteiro.")
    if not 1 <= numero <= QUANTIDADE_MAXIMA_POR_ITEM:
        raise ErroDeValidacao(
            f"A quantidade deve estar entre 1 e {QUANTIDADE_MAXIMA_POR_ITEM}."
        )
    return numero


def validar_distancia(distancia_km):
    """Valida a distancia de entrega: maior que zero e dentro da area de atendimento."""
    distancia = converter_para_dinheiro(distancia_km, "distancia")
    if distancia > DISTANCIA_MAXIMA_KM:
        raise ErroDeNegocio(
            f"Nao entregamos a mais de {DISTANCIA_MAXIMA_KM} km de distancia."
        )
    return distancia


def formatar_moeda(valor):
    """Formata um Decimal no padrao brasileiro. Exemplo: 1234.5 vira 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"  # Exemplo: '1,234.50' (padrao americano).
    # Trocamos os separadores usando um caractere temporario.
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"


# =============================================================================
# 4. MODELOS DE DADOS
# =============================================================================

@dataclass(frozen=True)  # frozen=True deixa o objeto imutavel apos criado.
class Cliente:
    """Representa o cliente. Os dados sao validados no momento da criacao."""

    nome: str
    telefone: str
    endereco: str

    def __post_init__(self):
        # Metodo especial chamado logo apos a criacao do objeto.
        # Como o objeto e imutavel, usamos object.__setattr__ para gravar os valores limpos.
        object.__setattr__(self, "nome", validar_nome(self.nome))
        object.__setattr__(self, "telefone", validar_telefone(self.telefone))
        object.__setattr__(self, "endereco", validar_endereco(self.endereco))

    def telefone_mascarado(self):
        """Exibe o telefone sem revelar todos os digitos (protecao de dados, LGPD)."""
        return f"({self.telefone[:2]}) *****-{self.telefone[-4:]}"


@dataclass(frozen=True)
class ItemCardapio:
    """Representa um produto vendido pelo restaurante."""

    codigo: str
    nome: str
    preco: Decimal

    def __post_init__(self):
        if not str(self.codigo).strip():
            raise ErroDeValidacao("O codigo do item nao pode ser vazio.")
        if not str(self.nome).strip():
            raise ErroDeValidacao("O nome do item nao pode ser vazio.")
        object.__setattr__(self, "preco", converter_para_dinheiro(self.preco, "preco"))


@dataclass(frozen=True)
class ItemPedido:
    """Representa um item do cardapio com a quantidade escolhida pelo cliente."""

    item: ItemCardapio
    quantidade: int

    @property  # Permite usar item_pedido.subtotal como se fosse um atributo.
    def subtotal(self):
        return self.item.preco * self.quantidade


class StatusPedido(Enum):
    """Etapas possiveis na vida de um pedido."""

    RASCUNHO = "Rascunho"
    CONFIRMADO = "Confirmado"
    EM_PREPARO = "Em preparo"
    SAIU_PARA_ENTREGA = "Saiu para entrega"
    ENTREGUE = "Entregue"
    CANCELADO = "Cancelado"


# Define quais mudancas de status sao permitidas (evita saltos ilogicos).
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
    """Concentra as regras de calculo e de status de um pedido."""

    def __init__(self, numero, cliente, distancia_km):
        self.numero = numero
        self.cliente = cliente
        self.distancia_km = validar_distancia(distancia_km)
        self.status = StatusPedido.RASCUNHO
        self._itens = []        # Lista interna de ItemPedido (o "_" indica uso interno).
        self._cupom = None      # Codigo do cupom aplicado, se houver.

    # ---------- Itens e cupom ----------

    def adicionar_item(self, item, quantidade):
        """Adiciona um item ao pedido. So e permitido enquanto o pedido e rascunho."""
        self._exigir_rascunho()
        quantidade = validar_quantidade(quantidade)

        # Se o item ja existe no pedido, somamos as quantidades em vez de duplicar a linha.
        for posicao, existente in enumerate(self._itens):
            if existente.item.codigo == item.codigo:
                nova_quantidade = existente.quantidade + quantidade
                validar_quantidade(nova_quantidade)  # Garante que o total respeita o limite.
                self._itens[posicao] = ItemPedido(item, nova_quantidade)
                return
        self._itens.append(ItemPedido(item, quantidade))

    def aplicar_cupom(self, codigo):
        """Aplica um cupom de desconto, caso o codigo seja valido."""
        self._exigir_rascunho()
        codigo = str(codigo).strip().upper()
        if codigo not in CUPONS:
            raise ErroDeNegocio(f"O cupom '{codigo}' e invalido ou expirou.")
        self._cupom = codigo

    # ---------- Calculos ----------

    @property
    def itens(self):
        return tuple(self._itens)  # Tupla impede alteracoes externas na lista.

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
        # Esta linha so e alcancada se as faixas e o limite maximo estiverem inconsistentes.
        raise ErroDeNegocio("Nao ha faixa de entrega para esta distancia.")

    @property
    def total(self):
        return self.subtotal - self.desconto + self.taxa_entrega

    # ---------- Status ----------

    def confirmar(self):
        """Confirma o pedido apos verificar as regras obrigatorias."""
        if not self._itens:
            raise ErroDeNegocio("O pedido precisa ter pelo menos um item.")
        if self.subtotal < PEDIDO_MINIMO:
            raise ErroDeNegocio(
                f"O pedido minimo e de {formatar_moeda(PEDIDO_MINIMO)}. "
                f"Faltam {formatar_moeda(PEDIDO_MINIMO - self.subtotal)}."
            )
        self._mudar_status(StatusPedido.CONFIRMADO)

    def avancar(self, novo_status):
        """Avanca o pedido para a proxima etapa, respeitando as transicoes permitidas."""
        self._mudar_status(novo_status)

    def cancelar(self):
        """Cancela o pedido. Nao e possivel cancelar apos a saida para entrega."""
        self._mudar_status(StatusPedido.CANCELADO)

    # ---------- Apoio interno ----------

    def _mudar_status(self, novo_status):
        if novo_status not in TRANSICOES_PERMITIDAS[self.status]:
            raise ErroDeNegocio(
                f"Nao e possivel mudar de '{self.status.value}' para '{novo_status.value}'."
            )
        self.status = novo_status

    def _exigir_rascunho(self):
        if self.status != StatusPedido.RASCUNHO:
            raise ErroDeNegocio("O pedido nao pode mais ser alterado apos a confirmacao.")

    def resumo(self):
        """Gera um texto com todos os valores detalhados (transparencia com o cliente)."""
        linhas = [
            f"Pedido No. {self.numero} - {self.status.value}",
            f"Cliente: {self.cliente.nome} | Telefone: {self.cliente.telefone_mascarado()}",
            f"Endereco: {self.cliente.endereco} ({str(self.distancia_km).replace('.', ',')} km)",
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
# 6. SERVICOS
# =============================================================================

class Cardapio:
    """Guarda os itens disponiveis e permite consulta-los pelo codigo."""

    def __init__(self):
        self._itens = {}  # Dicionario: codigo do item -> ItemCardapio.

    def adicionar(self, item):
        if item.codigo in self._itens:
            raise ErroDeNegocio(f"Ja existe um item com o codigo '{item.codigo}'.")
        self._itens[item.codigo] = item

    def buscar(self, codigo):
        codigo = str(codigo).strip().upper()
        if codigo not in self._itens:
            raise ErroDeNegocio(f"O item '{codigo}' nao existe no cardapio.")
        return self._itens[codigo]

    def listar(self):
        return list(self._itens.values())


class PedidoServico:
    """Cria e armazena pedidos, entregando a cada um um numero sequencial."""

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
        """Busca o item no cardapio pelo codigo e o adiciona ao pedido."""
        pedido.adicionar_item(self._cardapio.buscar(codigo), quantidade)


# =============================================================================
# 7. DEMONSTRACAO
# =============================================================================

def executar_e_mostrar_erro(descricao, acao):
    """Executa uma acao e exibe a mensagem caso uma regra seja violada."""
    try:
        acao()
        print(f"[OK]   {descricao}")
    except (ErroDeValidacao, ErroDeNegocio) as erro:
        print(f"[ERRO] {descricao}: {erro}")


def principal():
    # --- Monta o cardapio do restaurante ---
    cardapio = Cardapio()
    cardapio.adicionar(ItemCardapio("HB01", "Hamburguer Artesanal", "28.90"))
    cardapio.adicionar(ItemCardapio("PZ01", "Pizza Margherita", "45.00"))
    cardapio.adicionar(ItemCardapio("RF01", "Refrigerante Lata", "6.50"))
    cardapio.adicionar(ItemCardapio("SC01", "Suco Natural", "9.00"))

    print("=== CARDAPIO ===")
    for item in cardapio.listar():
        print(f"{item.codigo} - {item.nome}: {formatar_moeda(item.preco)}")

    servico = PedidoServico(cardapio)

    # --- Cenario 1: fluxo completo e bem-sucedido ---
    print("\n=== CENARIO 1: PEDIDO COMPLETO ===")
    cliente = Cliente("Maria da Silva", "(51) 99876-5432", "Rua das Flores, 120, Centro")
    pedido = servico.criar_pedido(cliente, "4.5")
    servico.adicionar_item_por_codigo(pedido, "HB01", 2)
    servico.adicionar_item_por_codigo(pedido, "RF01", 2)
    pedido.aplicar_cupom("primeira10")  # O codigo e normalizado para maiusculas.
    pedido.confirmar()
    pedido.avancar(StatusPedido.EM_PREPARO)
    print(pedido.resumo())

    # --- Cenario 2: frete gratis ---
    print("\n=== CENARIO 2: FRETE GRATIS ===")
    pedido2 = servico.criar_pedido(cliente, 2)
    servico.adicionar_item_por_codigo(pedido2, "PZ01", 3)
    pedido2.confirmar()
    print(pedido2.resumo())

    # --- Cenario 3: validacoes e regras sendo aplicadas ---
    print("\n=== CENARIO 3: ENTRADAS INVALIDAS E REGRAS DE NEGOCIO ===")
    executar_e_mostrar_erro(
        "Cliente com nome invalido",
        lambda: Cliente("A1", "51998765432", "Rua das Flores, 120"),
    )
    executar_e_mostrar_erro(
        "Cliente com telefone invalido",
        lambda: Cliente("Joao Pereira", "12345", "Rua das Flores, 120"),
    )
    executar_e_mostrar_erro(
        "Entrega fora da area de atendimento",
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
        "Item inexistente no cardapio",
        lambda: servico.adicionar_item_por_codigo(pedido3, "XX99", 1),
    )
    executar_e_mostrar_erro(
        "Cupom invalido",
        lambda: pedido3.aplicar_cupom("DESCONTAO"),
    )
    servico.adicionar_item_por_codigo(pedido3, "SC01", 1)
    executar_e_mostrar_erro(
        "Confirmacao abaixo do pedido minimo",
        pedido3.confirmar,
    )
    executar_e_mostrar_erro(
        "Cancelamento de pedido que ja saiu para entrega",
        lambda: (
            pedido.avancar(StatusPedido.SAIU_PARA_ENTREGA),
            pedido.cancelar(),
        ),
    )


if __name__ == "__main__":
    # Este bloco so executa quando o arquivo e rodado diretamente,
    # e nao quando ele e importado por outro arquivo.
    principal()
