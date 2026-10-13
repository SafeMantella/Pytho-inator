---
name: pytho-inator
description: Quando uma resposta terminou um trabalho repetível, sugere um CLI Python local que faz a tarefa inteira num comando. Dispara em pythonizer, pytho-inator, economizar tokens, /map-automation-opportunities e /check-skills. Não constrói nem testa sem um sim.
---

<!-- pytho-inator: skip -->

# Pytho-inator

O CLI faz a tarefa. O agente roda um comando e lê a última linha. Skill longa que reexplica os mesmos passos é token jogado fora. Uma chamada de CLI é leve, rápida, e pode rodar em paralelo com o resto do turno. Python entra porque é dinâmica: o tipo não é escrito no arquivo, então o script fica curto de gerar e de reler.

Executável neste projeto: `ferramentas/Pytho-inator/pytho-inator`. Dentro do repo: `./pytho-inator`.

O scanner só aponta. Quem decide é o agente. `shape=fan-out` é menu (ferramentas diferentes), não uma tarefa só. `judgment=keep` fica na skill. Não automatize aprovação, voz, gosto, estratégia ou entrevista.

## No fim de cada resposta

No Claude Code com o mod `pytho-inator` instalado, a linha já aparece debaixo da resposta. Não rode `glance` de novo.

Nos outros agentes (use `turn --cmd="<bash do turno>" <arquivos>` pra incluir os comandos que rodou):

1. Termine o pedido do Pedro.
2. Rode `ferramentas/Pytho-inator/pytho-inator glance` nos arquivos que você criou ou editou neste turno.
3. Stdout vazio: não escreva nada sobre isto.
4. Se houver uma linha: no máximo 3 linhas na resposta. Um CLI, a tarefa pronta na última linha do stdout. Pergunte `Quer que eu construa esse CLI?` Não construa neste turno.

## `/map-automation-opportunities`

1. Rode `ferramentas/Pytho-inator/pytho-inator map`.
2. Leia `references/cli-contract.md`.
3. Mostre no máximo 5. Prefira `shape=chain`. Descarte menu e julgamento.
4. Pare. Não construa, a menos que o Pedro já tenha pedido a construção nesta mesma mensagem.

## `/check-skills`

1. Rode `ferramentas/Pytho-inator/pytho-inator check`.
2. Leia `references/cli-contract.md`.
3. Para cada hit: o que o CLI substitui, e o que fica na skill quando `judgment=keep`.
4. Pare. Não edite a skill até o Pedro escolher uma.

## Construir (só depois de um sim)

Não pule passo. O CLI só nasce com a skill `ponytail` na intensidade **ultra**.

1. Leia `references/gates.md` e siga a ordem de lá.
2. Antes da primeira linha do CLI, leia a skill `ponytail` inteira e use a intensidade **ultra** até o arquivo existir. No Claude Code: `/ponytail ultra`. A escada copiada no gate 1 não substitui essa skill. Sem ela instalada: diga isso numa linha e siga só essa escada.
3. Se o caminho usa serviço pago, chave, ou cota que pode cobrar, pare e pergunte: `Esse caminho usa <serviço>, que é pago ou pode cobrar. Posso usar, ou sigo só com o que é grátis e local?` Sem sim, não instale e não chame.
4. Escreva o menor CLI que fecha a tarefa, ainda em ultra. A skill fica com uma linha: o comando.
5. Pergunte antes de rodar: `Posso testar <comando> agora? Ele <efeito>.` Sem sim, não rode. Isso inclui `--self-check`.

Não faça commit nem push sem pedido. Nada publicado sem aprovação.

Catálogo de tarefas chatas: *Automate the Boring Stuff with Python* (Al Sweigart, edição grátis). A tabela e a busca de biblioteca estão em `references/gates.md`. O livro diz **qual** tarefa vira programa. A escolha da biblioteca segue o passo 2 (ponytail ultra) e a stdlib, não a lista de deps do livro.
