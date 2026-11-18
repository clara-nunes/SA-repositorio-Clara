
# Devolutiva formativa — Atividade 01 da SA

**Estudante:** Clara  
**Turma:** Rio Negrinho — Manhã  
**Unidade Curricular:** Programação de Aplicativos  
**Projeto:** Delivery de Comida — Sistema de Pedidos  
**Código analisado:** `codigo/app.py`  
**Referência:** Situação de Aprendizagem nº 1 — *Da Ideia ao Código*

## O que você já conseguiu desenvolver

Clara, seu projeto apresenta uma estrutura bem organizada para simular pedidos de delivery, com cadastro de clientes, cardápio, itens, descontos, taxa de entrega e controle da situação dos pedidos.

Pontos positivos identificados:

- Utilizou **programação orientada a objetos**, com classes como `Cliente`, `ItemCardapio`, `ItemPedido`, `Pedido`, `Cardapio` e `PedidoServico`.
- Aplicou `dataclass` para representar dados e `Enum` para definir as situações possíveis dos pedidos.
- Criou **exceções específicas**, diferenciando dados inválidos de regras de negócio não atendidas.
- Utilizou `Decimal` para cálculos monetários, reduzindo problemas de precisão.
- Implementou validações de nome, telefone, endereço, quantidade e distância.
- Organizou regras de pedido mínimo, desconto, frete grátis e taxa de entrega.
- Definiu transições permitidas entre as situações dos pedidos.
- Incluiu cenários de demonstração que exercitam o funcionamento normal e situações inválidas.
- Utilizou docstrings e comentários explicativos que facilitam a compreensão do código.

## O que precisa ser corrigido

### 1. Corrigir a instrução de execução

No início do código, a documentação informa o comando `python delivery.py`, mas o arquivo disponibilizado está em `codigo/app.py`.

**Como melhorar:** atualizar a instrução para corresponder à organização real do repositório. Verifique se outro estudante conseguiria executar o projeto apenas seguindo a documentação.

### 2. Tornar o tratamento de erros mais específico

Na função `converter_para_dinheiro()`, a conversão utiliza `except Exception`. Essa abordagem captura uma variedade muito grande de problemas, inclusive alguns não relacionados diretamente à entrada numérica.

**Como melhorar:** tratar as exceções esperadas da conversão, como `InvalidOperation`, `ValueError` e `TypeError`, conforme o caso. Isso facilita a identificação de falhas inesperadas durante o desenvolvimento.

## Oportunidades de melhoria

### 3. Separar as responsabilidades em módulos

O código já está dividido em classes e funções, mas permanece concentrado em um único arquivo.

**Como melhorar:** considerar módulos específicos para modelos de dados, validações, regras de pedidos e demonstração. Isso facilitará a manutenção e os testes.

### 4. Evoluir a demonstração para interação com o usuário

A função `principal()` apresenta cenários de uso com dados previamente definidos. Essa estratégia é útil para comprovar o funcionamento inicial.

**Como melhorar:** na continuidade do projeto, permitir que o usuário escolha produtos e quantidades, informe dados e acompanhe o pedido. Preserve as regras já implementadas, evitando duplicá-las na futura interface.

### 5. Transformar os cenários em testes automatizados

Os cenários atuais demonstram casos válidos e inválidos. Entretanto, a exibição de mensagens não substitui completamente testes que verificam o resultado esperado.

**Como melhorar:** criar testes com `assert` ou `unittest` para os cálculos e as validações. Assim, será possível detectar regressões após alterações.

### 6. Melhorar a documentação específica do projeto

O código possui uma introdução detalhada, mas o README pode explicar melhor a aplicação desenvolvida.

**Como melhorar:** incluir instruções de execução, funcionalidades implementadas, regras de negócio e exemplos dos testes realizados.

## Testes recomendados

1. Criar um pedido válido e confirmar seu valor final.
2. Tentar cadastrar cliente com nome ou telefone inválido.
3. Adicionar quantidade negativa ou superior ao limite permitido.
4. Aplicar cupom válido e inválido.
5. Verificar as diferentes faixas de taxa de entrega.
6. Confirmar pedido abaixo do valor mínimo.
7. Tentar modificar um pedido já confirmado.
8. Testar transições permitidas e proibidas entre as situações.
9. Conferir os resultados de arredondamento monetário.

## Prioridades para a próxima versão

1. **Corrigir a documentação de execução.**
2. **Utilizar exceções específicas nas conversões.**
3. **Criar testes automatizados para as regras principais.**
4. **Separar gradualmente os módulos da aplicação.**
5. **Preparar a interação do usuário sem duplicar as regras de negócio.**

## Mensagem final

Clara, seu trabalho demonstra compreensão de **orientação a objetos, validação, organização de responsabilidades e construção de regras de negócio**. A utilização de `Decimal`, exceções específicas e controle de situações é um ponto positivo importante.

Continue desenvolvendo o projeto com foco na testabilidade, na documentação e na reutilização do código. Você construiu uma base organizada para as próximas etapas da Situação de Aprendizagem.
