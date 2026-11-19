
# Devolutiva formativa — Atividade 02 da SA

**Estudante:** Clara Lis Nunes  
**Turma:** Rio Negrinho — Manhã  
**Unidade Curricular:** Programação de Aplicativos  
**Projeto:** Delivery de Comida — Sistema de Pedidos  
**Atividade:** Interface funcional  
**Arquivos analisados:** `interface/interface.py`, `interface/delivery.py` e `codigo/app.py`

## O que você já conseguiu desenvolver

Clara, a nova versão do seu projeto apresenta uma **interface gráfica em Tkinter conectada às regras de negócio do delivery**.

A organização demonstra preocupação com a separação de responsabilidades e com a manutenção do código.

Pontos positivos identificados:

- Criou a classe `AppDelivery` para organizar a aplicação gráfica.
- Separou a lógica do sistema no arquivo `delivery.py`.
- Utilizou componentes Tkinter como `Entry`, `Combobox`, `Treeview`, botões e abas.
- Implementou ações para iniciar pedidos, adicionar itens, aplicar cupons, confirmar e cancelar pedidos.
- Criou um histórico visual de operações e mensagens de erro.
- Apresentou subtotal, desconto, taxa de entrega e total.
- Reaproveitou classes e funções já desenvolvidas na primeira atividade.
- Utilizou exceções específicas para apresentar erros ao usuário.
- Documentou classes, métodos e funções.

## O que foi ajustado desde a última devolutiva

### 1. Interface interativa — ATENDIDO

Na Atividade 01, foi recomendado substituir gradualmente os cenários demonstrativos por interações reais.

Agora, `interface.py` recebe dados digitados pelo usuário e executa operações de pedidos.

**Evolução positiva:** as ações da interface chamam métodos da lógica desenvolvida no projeto.

### 2. Separação das responsabilidades — ATENDIDO

A recomendação anterior era separar a lógica em módulos.

Agora existem arquivos específicos para a interface e para as regras de negócio.

**Evolução positiva:** a classe gráfica não precisa repetir os cálculos de frete, desconto e total.

### 3. Tratamento de exceções — PARCIALMENTE ATENDIDO

A interface utiliza tratamento específico para `ErroDeValidacao` e `ErroDeNegocio`.

Entretanto, a função `converter_para_dinheiro()` da lógica ainda utiliza um tratamento genérico com `except Exception`.

**Como melhorar:** substituir por exceções específicas esperadas na conversão.

### 4. Documentação — PARCIALMENTE ATENDIDO

O novo arquivo da interface possui uma introdução que explica seu funcionamento e o comando de execução.

**Como melhorar:** atualizar também o README principal e esclarecer a relação entre `codigo/app.py` e `interface/delivery.py`.

## O que precisa ser corrigido

### 5. Evitar duas cópias das regras de negócio

O repositório agora possui duas versões semelhantes da lógica de delivery.

**Como melhorar:** definir uma única implementação principal e fazer a interface importar essa versão. Isso evita diferenças futuras entre cálculos e validações.

### 6. Ampliar os testes automatizados

Os cenários de demonstração existentes são úteis, mas ainda podem ser transformados em testes que conferem resultados automaticamente.

**Como melhorar:** utilizar `assert` ou `unittest` para validar cálculos monetários, cupons, limites de quantidade e transições entre situações.

### 7. Revisar a documentação de execução

**Como melhorar:** informar claramente que a interface deve ser iniciada pelo arquivo `interface/interface.py`, com `delivery.py` disponível para importação na mesma pasta.

## Testes recomendados

1. Executar a interface utilizando o comando documentado.
2. Informar nome, telefone e endereço inválidos.
3. Iniciar um pedido e adicionar dois produtos diferentes.
4. Aplicar cupons válidos e inválidos.
5. Confirmar um pedido abaixo do valor mínimo.
6. Verificar o cálculo do frete nas diferentes distâncias.
7. Avançar as situações do pedido até a conclusão.
8. Tentar cancelar um pedido em situação não permitida.
9. Conferir o histórico de mensagens após cada operação.
10. Executar os mesmos cálculos diretamente em `delivery.py`.

## Prioridades para a próxima versão

1. **Manter a separação entre interface e lógica.**
2. **Eliminar a duplicação de regras de negócio.**
3. **Substituir tratamentos genéricos de exceções.**
4. **Criar testes automatizados das regras principais.**
5. **Atualizar o README com as instruções da interface.**

## Mensagem final

Clara, você realizou uma evolução significativa em relação à entrega anterior.

A interface gráfica agora utiliza as regras de negócio do próprio sistema, demonstrando aplicação de modularização, orientação a objetos e tratamento de erros.

Continue aprimorando a reutilização do código e a testabilidade. A estrutura atual é uma boa base para as próximas etapas da Situação de Aprendizagem.
