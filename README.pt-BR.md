# Pytho-inator

Skill de agente que transforma uma tarefa chata e determinística num CLI Python local e grátis. O agente roda um comando e lê a última linha. Não repensa os passos.

Este arquivo é a versão em português do [README.md](README.md). O procedimento que o agente segue está em [`skills/pytho-inator/SKILL.md`](skills/pytho-inator/SKILL.md).

## Instalar

Cole isto no Claude Code:

```
Instala a skill https://github.com/SafeMantella/Pytho-inator no Claude Code, global. Não é plugin.
```

## Por quê

Uma skill que dita cinco comandos de shell gasta token toda vez que o agente a lê, e ainda pode pular um passo. Um CLI que termina a tarefa gasta um comando. Se um comando resolve, a skill encolhe até esse comando.

O ponto é economizar token. Uma chamada de CLI é leve e rápida, e o Claude pode rodá-la em paralelo com outras tarefas no mesmo turno. Python mantém essa chamada barata na ida e na volta: a linguagem é dinâmica, o tipo não é escrito no arquivo, e o script fica curto de gerar e curto de reler.

O scanner não decide. Ele imprime uma dica curta. O agente descarta menu (`fan-out`) e o que for gosto, aprovação, voz ou estratégia (`judgment=keep`).

## No fim de uma resposta

Qualquer agente, inclusive o Claude Code, roda o `glance` no fim de uma resposta que criou ou editou arquivo:

```bash
./pytho-inator glance caminho/do/arquivo.md
```

Stdout vazio é silêncio. Um hit são no máximo três linhas e a pergunta "quer que eu construa?". Não constrói no mesmo turno.

Essa frase precisa estar nas instruções que o agente lê sempre. A descrição da skill sozinha não dispara depois de toda resposta.

## Comandos

| Comando | O que o agente faz |
|---|---|
| `/map-automation-opportunities` | `pytho-inator map`. Onde um CLI novo substitui uma cadeia. |
| `/check-skills` | `pytho-inator check`. Onde uma skill existente encolhe até um comando. |

Os dois param antes de escrever código. Construir só começa depois de um sim, e aí segue [`skills/pytho-inator/references/gates.md`](skills/pytho-inator/references/gates.md).

## O CLI

Só stdlib. Sem chave. O `uv` roda; `python3` é o fallback.

```bash
./pytho-inator map [raiz]       # dicas ordenadas, padrão 5
./pytho-inator check [raiz]     # ponto de inserção em cada skill
./pytho-inator glance [arquivos]  # calado, a menos que um arquivo tocado esconda uma cadeia
./pytho-inator vet nome [nome]  # licença, versão e data na API JSON do PyPI
./pytho-inator self-check       # asserts offline
```

`map` e `check` olham `.claude/skills`, `.claude/commands`, `skills/` e `commands/`. Não varrem o resto da árvore. `glance` sem caminhos usa `git status` e só skill ou comando alterado. Não imprime nada sem repositório, ou sem essa mudança. Passe o caminho quando a tarefa está em outro arquivo.

`vet` imprime `ok` ou `check`. `quiet-Nd` significa que o último upload tem mais de 24 meses; licença conhecida continua `ok`. `check` é licença ausente, release yanked, ou erro do PyPI. Olhe antes de depender.

## Regras do que ele constrói

- **Ponytail ultra** no momento de escrever o CLI. Ler a skill ponytail instalada e ligar a intensidade ultra (`/ponytail ultra` no Claude Code) antes da primeira linha. Stdlib primeiro. Um arquivo. Sem framework. A escada curta em `gates.md` é só o fallback quando essa skill não está instalada.
- **uv** pro interpretador e pras dependências, no venv daquela ferramenta. Nunca o Python do sistema.
- **Grátis e open source.** MIT, Apache ou BSD quando duas bibliotecas servem igual.
- **Perguntar antes de qualquer API paga**, serviço com chave, ou conta que pode cobrar. Cota grátis com cartão conta como pago. Esperar o sim.
- **Perguntar antes de testar** o que acabou de ser escrito, inclusive o `--self-check`.
- ***Automate the Boring Stuff with Python*** (Al Sweigart, edição grátis) é o catálogo de tarefas: arquivos, texto, CSV, JSON, planilha, PDF, Word, imagem, página web, tempo, e-mail, GUI. O livro nomeia a tarefa. Não é lista de dependência, e o texto dele não é copiado aqui. O mapa está em [`gates.md`](skills/pytho-inator/references/gates.md).
- Achar biblioteca é busca web grátis mais `vet`. Não gastar um pipeline de pesquisa pago pra escolher um nome de pacote.

## Layout

```
pytho-inator          wrapper (uv, depois python3)
pytho_inator.py       o scanner
skills/pytho-inator/  a skill do agente
commands/             /map-automation-opportunities e /check-skills
```

## Licença

MIT. Ver [LICENSE](LICENSE).
