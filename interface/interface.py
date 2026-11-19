"""
Interface gráfica (Tkinter) do Sistema de Delivery.

Objetivo:
    Receber dados do usuário, executar a lógica do arquivo delivery.py e
    informar o resultado de cada ação (sucesso ou motivo da recusa).

Princípio de projeto:
    A interface NÃO tem regras de negócio. Ela só lê os campos, chama as classes
    de delivery.py e mostra o que voltou. Assim, toda validação continua em um
    único lugar (delivery.py) e a interface apenas exibe as mensagens de erro.

Organização do arquivo:
    1. Cardápio inicial
    2. Classe AppDelivery
         - construção da tela (métodos _criar_*)
         - ações do usuário (métodos acao_*)
         - apoio: execução protegida, log e atualização da tela

Cuidados éticos (CS1 a CS3):
    - Transparência: subtotal, desconto, taxa e total ficam sempre visíveis.
    - Privacidade (LGPD): o telefone é exibido mascarado.
    - Honestidade: toda recusa mostra o motivo, nada falha em silêncio.

Como executar (delivery.py precisa estar na mesma pasta):
    python interface.py
"""

import tkinter as tk
from datetime import datetime
from decimal import Decimal
from tkinter import font, messagebox, ttk

from delivery import (
    DISTANCIA_MAXIMA_KM,
    PEDIDO_MINIMO,
    QUANTIDADE_MAXIMA_POR_ITEM,
    TRANSICOES_PERMITIDAS,
    Cardapio,
    Cliente,
    ErroDeNegocio,
    ErroDeValidacao,
    ItemCardapio,
    PedidoServico,
    StatusPedido,
    formatar_moeda,
)

# Cores usadas no log e na barra de status.
COR_OK = "#1b7f3b"
COR_ERRO = "#c62828"
COR_INFO = "#555555"


# =============================================================================
# 1. CARDÁPIO INICIAL
# =============================================================================

def montar_cardapio():
    """Cria o cardápio do restaurante (os mesmos itens da demonstração)."""
    cardapio = Cardapio()
    cardapio.adicionar(ItemCardapio("HB01", "Hamburguer Artesanal", "28.90"))
    cardapio.adicionar(ItemCardapio("PZ01", "Pizza Margherita", "45.00"))
    cardapio.adicionar(ItemCardapio("RF01", "Refrigerante Lata", "6.50"))
    cardapio.adicionar(ItemCardapio("SC01", "Suco Natural", "9.00"))
    return cardapio


# =============================================================================
# 2. CLASSE PRINCIPAL DA INTERFACE
# =============================================================================

class AppDelivery(tk.Tk):
    """Janela principal: formulário à esquerda, pedido e histórico à direita."""

    def __init__(self):
        super().__init__()
        self.title("Delivery - Realização de Pedidos")
        self.geometry("1040x700")
        self.minsize(920, 620)
        ttk.Style(self).theme_use("clam")

        # Fonte em negrito reaproveitada em vários rótulos.
        self.fonte_negrito = font.nametofont("TkDefaultFont").copy()
        self.fonte_negrito.configure(weight="bold")

        # Objetos da lógica (delivery.py). O pedido só existe após "Iniciar pedido".
        self.cardapio = montar_cardapio()
        self.servico = PedidoServico(self.cardapio)
        self.pedido = None

        # Mapa "texto exibido na lista" -> "código do item", usado no Combobox.
        self.rotulos_itens = {
            f"{i.codigo} - {i.nome} ({formatar_moeda(i.preco)})": i.codigo
            for i in self.cardapio.listar()
        }

        # Variáveis ligadas aos campos: lemos o texto digitado com .get().
        self.var_nome = tk.StringVar()
        self.var_telefone = tk.StringVar()
        self.var_endereco = tk.StringVar()
        self.var_distancia = tk.StringVar()
        self.var_item = tk.StringVar()
        self.var_quantidade = tk.StringVar(value="1")
        self.var_cupom = tk.StringVar()

        self._criar_layout()
        self._registrar("INFO", "Sistema pronto. Preencha os dados do cliente e inicie o pedido.")
        self._atualizar_tela()

    # -------------------------------------------------------------------------
    # Construção da tela
    # -------------------------------------------------------------------------

    def _criar_layout(self):
        """Divide a janela em coluna esquerda (entradas) e direita (resultados)."""
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        esquerda = ttk.Frame(self, padding=10)
        esquerda.grid(row=0, column=0, sticky="ns")
        direita = ttk.Frame(self, padding=(0, 10, 10, 10))
        direita.grid(row=0, column=1, sticky="nsew")
        direita.columnconfigure(0, weight=1)
        direita.rowconfigure(0, weight=3)
        direita.rowconfigure(1, weight=2)

        self._criar_painel_cliente(esquerda)
        self._criar_painel_itens(esquerda)
        self._criar_painel_acoes(esquerda)
        self._criar_painel_pedido(direita)
        self._criar_painel_log(direita)

        # Barra de status: mostra o resultado da última ação.
        self.lbl_barra = ttk.Label(self, text="", anchor="w", padding=(10, 4))
        self.lbl_barra.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _criar_painel_cliente(self, pai):
        quadro = ttk.LabelFrame(pai, text=" 1. Cliente e entrega ", padding=10)
        quadro.pack(fill="x", pady=(0, 10))

        campos = [
            ("Nome", self.var_nome),
            ("Telefone (com DDD)", self.var_telefone),
            ("Endereço (rua, nº, bairro)", self.var_endereco),
            (f"Distância em km (máx. {DISTANCIA_MAXIMA_KM})", self.var_distancia),
        ]
        self.entradas_cliente = []  # Guardadas para poder bloqueá-las depois.
        for linha, (rotulo, variavel) in enumerate(campos):
            ttk.Label(quadro, text=rotulo).grid(row=linha * 2, column=0, sticky="w")
            entrada = ttk.Entry(quadro, textvariable=variavel, width=38)
            entrada.grid(row=linha * 2 + 1, column=0, sticky="ew", pady=(0, 6))
            self.entradas_cliente.append(entrada)

        self.btn_iniciar = ttk.Button(quadro, text="Iniciar pedido", command=self.acao_iniciar_pedido)
        self.btn_iniciar.grid(row=8, column=0, sticky="ew", pady=(4, 0))

    def _criar_painel_itens(self, pai):
        quadro = ttk.LabelFrame(pai, text=" 2. Itens e cupom ", padding=10)
        quadro.pack(fill="x", pady=(0, 10))

        ttk.Label(quadro, text="Item do cardápio").grid(row=0, column=0, columnspan=2, sticky="w")
        self.combo_item = ttk.Combobox(
            quadro, textvariable=self.var_item, values=list(self.rotulos_itens),
            state="readonly", width=36,
        )
        self.combo_item.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(quadro, text=f"Quantidade (1 a {QUANTIDADE_MAXIMA_POR_ITEM})").grid(row=2, column=0, sticky="w")
        self.spin_qtd = ttk.Spinbox(quadro, textvariable=self.var_quantidade, from_=1,
                                    to=QUANTIDADE_MAXIMA_POR_ITEM, width=6)
        self.spin_qtd.grid(row=3, column=0, sticky="w", pady=(0, 6))
        self.btn_adicionar = ttk.Button(quadro, text="Adicionar item", command=self.acao_adicionar_item)
        self.btn_adicionar.grid(row=3, column=1, sticky="e", pady=(0, 6))

        ttk.Label(quadro, text="Cupom de desconto").grid(row=4, column=0, columnspan=2, sticky="w")
        self.entrada_cupom = ttk.Entry(quadro, textvariable=self.var_cupom, width=20)
        self.entrada_cupom.grid(row=5, column=0, sticky="w")
        self.btn_cupom = ttk.Button(quadro, text="Aplicar cupom", command=self.acao_aplicar_cupom)
        self.btn_cupom.grid(row=5, column=1, sticky="e")

        quadro.columnconfigure(0, weight=1)

    def _criar_painel_acoes(self, pai):
        quadro = ttk.LabelFrame(pai, text=" 3. Andamento do pedido ", padding=10)
        quadro.pack(fill="x")

        self.btn_confirmar = ttk.Button(quadro, text="Confirmar pedido", command=self.acao_confirmar)
        self.btn_avancar = ttk.Button(quadro, text="Avançar etapa", command=self.acao_avancar)
        self.btn_cancelar = ttk.Button(quadro, text="Cancelar pedido", command=self.acao_cancelar)
        self.btn_novo = ttk.Button(quadro, text="Novo pedido", command=self.acao_novo_pedido)
        for botao in (self.btn_confirmar, self.btn_avancar, self.btn_cancelar, self.btn_novo):
            botao.pack(fill="x", pady=2)

    def _criar_painel_pedido(self, pai):
        """Abas da direita: tabela com os totais e o resumo completo em texto."""
        abas = ttk.Notebook(pai)
        abas.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        aba_pedido = ttk.Frame(abas, padding=8)
        aba_resumo = ttk.Frame(abas, padding=8)
        abas.add(aba_pedido, text="Pedido")
        abas.add(aba_resumo, text="Resumo completo")

        # --- Aba "Pedido": situação, tabela de itens e totais ---
        self.lbl_status = ttk.Label(aba_pedido, font=self.fonte_negrito)
        self.lbl_status.pack(anchor="w")
        self.lbl_cliente = ttk.Label(aba_pedido, wraplength=560, foreground=COR_INFO)
        self.lbl_cliente.pack(anchor="w", pady=(0, 6))

        self.tabela = ttk.Treeview(aba_pedido, columns=("qtd", "item", "subtotal"),
                                   show="headings", height=6)
        self.tabela.heading("qtd", text="Qtd")
        self.tabela.heading("item", text="Item")
        self.tabela.heading("subtotal", text="Subtotal")
        self.tabela.column("qtd", width=50, anchor="center", stretch=False)
        self.tabela.column("item", width=300)
        self.tabela.column("subtotal", width=110, anchor="e", stretch=False)
        self.tabela.pack(fill="both", expand=True)

        # Totais sempre visíveis (transparência com o cliente).
        totais = ttk.Frame(aba_pedido, padding=(0, 8, 0, 0))
        totais.pack(fill="x")
        totais.columnconfigure(0, weight=1)
        self.var_totais = {}
        for linha, chave in enumerate(("Subtotal", "Desconto", "Taxa de entrega", "TOTAL")):
            negrito = chave == "TOTAL"
            self.var_totais[chave] = tk.StringVar()
            ttk.Label(totais, text=chave, font=self.fonte_negrito if negrito else None).grid(
                row=linha, column=0, sticky="e", padx=8)
            ttk.Label(totais, textvariable=self.var_totais[chave], width=14, anchor="e",
                      font=self.fonte_negrito if negrito else None).grid(row=linha, column=1, sticky="e")
        self.lbl_dica = ttk.Label(aba_pedido, foreground=COR_INFO)
        self.lbl_dica.pack(anchor="w", pady=(6, 0))

        # --- Aba "Resumo completo": texto gerado por Pedido.resumo() ---
        self.texto_resumo = tk.Text(aba_resumo, state="disabled", wrap="word", font="TkFixedFont")
        self.texto_resumo.pack(fill="both", expand=True)

    def _criar_painel_log(self, pai):
        quadro = ttk.LabelFrame(pai, text=" Histórico de ações ", padding=6)
        quadro.grid(row=1, column=0, sticky="nsew")
        quadro.columnconfigure(0, weight=1)
        quadro.rowconfigure(0, weight=1)

        self.log = tk.Text(quadro, height=8, state="disabled", wrap="word")
        rolagem = ttk.Scrollbar(quadro, command=self.log.yview)
        self.log.configure(yscrollcommand=rolagem.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        rolagem.grid(row=0, column=1, sticky="ns")
        # Tags de cor: cada tipo de mensagem tem a sua.
        self.log.tag_configure("OK", foreground=COR_OK)
        self.log.tag_configure("ERRO", foreground=COR_ERRO)
        self.log.tag_configure("INFO", foreground=COR_INFO)

    # -------------------------------------------------------------------------
    # Ações do usuário (cada uma chama a lógica de delivery.py)
    # -------------------------------------------------------------------------

    def acao_iniciar_pedido(self):
        """Valida os dados do cliente (classe Cliente) e cria o pedido."""
        def acao():
            cliente = Cliente(self.var_nome.get(), self.var_telefone.get(), self.var_endereco.get())
            self.pedido = self.servico.criar_pedido(cliente, self.var_distancia.get())
            return f"Pedido nº {self.pedido.numero} criado para {cliente.nome}."
        self._executar("Iniciar pedido", acao)

    def acao_adicionar_item(self):
        """Adiciona o item escolhido com a quantidade informada."""
        def acao():
            codigo = self.rotulos_itens.get(self.var_item.get())
            if codigo is None:
                raise ErroDeValidacao("Selecione um item do cardápio.")
            # A quantidade chega como texto; validar_quantidade() converte e valida.
            self.servico.adicionar_item_por_codigo(self.pedido, codigo, self.var_quantidade.get())
            return f"Item {codigo} adicionado (quantidade informada: {self.var_quantidade.get()})."
        self._executar("Adicionar item", acao)

    def acao_aplicar_cupom(self):
        """Aplica o cupom digitado; a lógica recusa códigos inválidos."""
        def acao():
            self.pedido.aplicar_cupom(self.var_cupom.get())
            return f"Cupom aplicado. Desconto atual: {formatar_moeda(self.pedido.desconto)}."
        self._executar("Aplicar cupom", acao)

    def acao_confirmar(self):
        """Confirma o pedido; a lógica exige itens e o pedido mínimo."""
        def acao():
            self.pedido.confirmar()
            return f"Pedido confirmado. Total: {formatar_moeda(self.pedido.total)}."
        self._executar("Confirmar pedido", acao)

    def acao_avancar(self):
        """Move o pedido para a próxima etapa permitida (preparo, entrega...)."""
        def acao():
            proximo = self._proximo_status()
            self.pedido.avancar(proximo)
            return f"Pedido avançou para '{proximo.value}'."
        self._executar("Avançar etapa", acao)

    def acao_cancelar(self):
        """Pede confirmação ao usuário antes de cancelar (ação sem volta)."""
        if not messagebox.askyesno("Cancelar pedido", "Deseja realmente cancelar este pedido?"):
            return

        def acao():
            self.pedido.cancelar()
            return "Pedido cancelado."
        self._executar("Cancelar pedido", acao)

    def acao_novo_pedido(self):
        """Descarta o pedido atual e libera o formulário para um novo."""
        self.pedido = None
        self.var_item.set("")
        self.var_quantidade.set("1")
        self.var_cupom.set("")
        self._registrar("INFO", "Formulário liberado para um novo pedido.")
        self._atualizar_tela()

    # -------------------------------------------------------------------------
    # Apoio: execução protegida, log e atualização da tela
    # -------------------------------------------------------------------------

    def _executar(self, descricao, acao):
        """Roda uma ação e informa o resultado.

        Se a lógica lançar ErroDeValidacao (dado inválido) ou ErroDeNegocio
        (regra não atendida), a mensagem vai para o log e a barra de status,
        e a tela continua consistente. Cada ação devolve o texto de sucesso.
        """
        try:
            mensagem = acao()
        except (ErroDeValidacao, ErroDeNegocio) as erro:
            self._registrar("ERRO", f"{descricao}: {erro}")
        else:
            self._registrar("OK", mensagem)
        self._atualizar_tela()

    def _registrar(self, tipo, mensagem):
        """Grava a mensagem no histórico (com horário) e na barra de status."""
        hora = datetime.now().strftime("%H:%M:%S")
        rotulo = {"OK": "[OK]  ", "ERRO": "[ERRO]", "INFO": "[INFO]"}[tipo]
        self.log.configure(state="normal")
        self.log.insert("end", f"{hora} {rotulo} {mensagem}\n", tipo)
        self.log.see("end")  # Rola até a mensagem mais recente.
        self.log.configure(state="disabled")
        cor = {"OK": COR_OK, "ERRO": COR_ERRO, "INFO": COR_INFO}[tipo]
        self.lbl_barra.configure(text=f"{rotulo} {mensagem}", foreground=cor)

    def _proximo_status(self):
        """Próxima etapa do fluxo normal (a que não é cancelamento), ou None."""
        opcoes = TRANSICOES_PERMITIDAS[self.pedido.status] - {StatusPedido.CANCELADO}
        return next(iter(opcoes), None)

    @staticmethod
    def _habilitar(widgets, ativo, estado_ativo="normal"):
        """Liga ou desliga um grupo de widgets de uma vez."""
        for w in widgets:
            w.configure(state=estado_ativo if ativo else "disabled")

    @staticmethod
    def _escrever(caixa, texto):
        """Troca o conteúdo de uma caixa de texto somente leitura."""
        caixa.configure(state="normal")
        caixa.delete("1.0", "end")
        caixa.insert("1.0", texto)
        caixa.configure(state="disabled")

    def _atualizar_tela(self):
        """Redesenha tudo a partir do estado do pedido (única fonte da verdade)."""
        pedido = self.pedido
        existe = pedido is not None
        rascunho = existe and pedido.status == StatusPedido.RASCUNHO

        # Quais controles ficam ativos em cada situação.
        self._habilitar(self.entradas_cliente, not existe)
        self._habilitar([self.btn_iniciar], not existe)
        self._habilitar([self.combo_item], rascunho, "readonly")
        self._habilitar([self.spin_qtd, self.entrada_cupom, self.btn_adicionar,
                         self.btn_cupom, self.btn_confirmar], rascunho)
        self._habilitar([self.btn_avancar], existe and not rascunho and self._proximo_status() is not None)
        self._habilitar([self.btn_cancelar], existe and StatusPedido.CANCELADO in TRANSICOES_PERMITIDAS[pedido.status])
        self._habilitar([self.btn_novo], existe)

        # Limpa a tabela e a redesenha com os itens atuais.
        self.tabela.delete(*self.tabela.get_children())
        zero = formatar_moeda(Decimal("0.00"))

        if not existe:
            self.lbl_status.configure(text="Nenhum pedido em andamento")
            self.lbl_cliente.configure(text="")
            for var in self.var_totais.values():
                var.set(zero)
            self.lbl_dica.configure(text="Preencha os dados do cliente e clique em 'Iniciar pedido'.")
            self._escrever(self.texto_resumo, "Nenhum pedido em andamento.")
            return

        c = pedido.cliente
        self.lbl_status.configure(text=f"Pedido nº {pedido.numero} - {pedido.status.value}")
        self.lbl_cliente.configure(
            text=f"{c.nome} | {c.telefone_mascarado()} | {c.endereco} ({pedido.distancia_km} km)")
        for i in pedido.itens:
            self.tabela.insert("", "end", values=(i.quantidade, i.item.nome, formatar_moeda(i.subtotal)))

        self.var_totais["Subtotal"].set(formatar_moeda(pedido.subtotal))
        self.var_totais["Desconto"].set("-" + formatar_moeda(pedido.desconto))
        self.var_totais["Taxa de entrega"].set(formatar_moeda(pedido.taxa_entrega))
        self.var_totais["TOTAL"].set(formatar_moeda(pedido.total))

        # Dica de pedido mínimo enquanto o pedido ainda pode ser alterado.
        if rascunho and pedido.subtotal < PEDIDO_MINIMO:
            falta = formatar_moeda(PEDIDO_MINIMO - pedido.subtotal)
            self.lbl_dica.configure(text=f"Faltam {falta} para atingir o pedido mínimo.")
        else:
            self.lbl_dica.configure(text="")
        self._escrever(self.texto_resumo, pedido.resumo())


if __name__ == "__main__":
    # Só abre a janela quando o arquivo é executado diretamente.
    AppDelivery().mainloop()