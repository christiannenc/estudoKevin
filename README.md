# Ajudando o Kevin a estudar

Site estático com exercícios de estudo para o Kevin: quizzes HTML interativos e folhas para imprimir em PDF, organizados por matéria.

HTML/CSS/JS puro — sem build step, sem framework, sem dependências. O ponto forte do projeto é a simplicidade: adicionar um exercício novo é soltar um arquivo na pasta certa e atualizar o `manifest.json`.

## Estrutura

```
index.html         → página inicial (lista as matérias em acordeão)
manifest.json      → fonte de dados: lista de exercícios por matéria
assets/
  style.css        → estilo compartilhado (tema escuro)
  mascote.svg      → mascote original do site
materias/
  {materia}/
    {arquivo}.html ou .pdf   → os exercícios em si
```

O `index.html` lê o `manifest.json` e monta a lista de cards. **O título exibido em cada card é gerado automaticamente pelo JS a partir do nome do arquivo** — não existe título escrito à mão em lugar nenhum.

## Convenção de nome de arquivo

Todo exercício segue este padrão:

```
{tipo}_{materia}_{ano}_tri{N}_{descricao_livre}_{parcial|completa}_v{N}.{html|pdf}
```

Exemplo: `quiz_portugues_2026_tri2_prova_parcial_v1.html`

| Parte | O que é |
| --- | --- |
| `tipo` | Livre (`quiz`, `prova`, `redacao`, …) — só organizacional, não entra no parsing |
| `materia` | Bate com a chave da matéria no `manifest.json` |
| `ano` | Ano letivo |
| `tri{N}` | Trimestre (`tri1`, `tri2`, `tri3`) |
| `descricao_livre` | Qualquer coisa — não entra no título gerado |
| `parcial` / `completa` | Se é uma versão reduzida ou completa do conteúdo |
| `v{N}` | Número da versão |

A extensão decide o badge e o comportamento do link:

- `.html` → badge **Quiz**, abre em nova aba
- `.pdf` → badge **Imprimir**, abre na mesma aba

**Cada versão é um exercício separado, não substitui a anterior.** A v1 e a v2 do mesmo trimestre aparecem como dois cards distintos, e o título gerado sempre inclui a versão para diferenciá-los (ex: "2º trimestre 2026 · Parcial · v1").

## Histórico de pontuação

Cada card de quiz mostra o histórico das tentativas anteriores e um badge indicando se já foi feito. O histórico fica no `localStorage` do navegador (chave: nome do arquivo; valor: array de `{score, total, date}`) — este é o **único** uso de armazenamento local no projeto.

Os cards dentro de cada matéria são ordenados assim:

1. Não feitos primeiro
2. Depois, mais recentes primeiro (ano + trimestre + versão, do maior para o menor)

PDFs não têm histórico, então contam sempre como "não feitos" na ordenação.

## Como adicionar um exercício novo

1. Salvar o arquivo em `materias/{materia}/` seguindo a convenção de nome acima. Se a matéria ainda não existe, criar a pasta e a entrada no manifest.
2. Adicionar uma entrada nova no array `exercicios` da matéria em `manifest.json`:
   ```json
   {
     "arquivo": "materias/portugues/quiz_portugues_2026_tri2_prova_parcial_v2.html",
     "assunto": "Resumo curto dos tópicos cobertos no exercício"
   }
   ```
   O `assunto` é o único texto digitado à mão — normalmente sai da primeira página do material.
3. Commit e push. O deploy no Vercel é automático.

Quizzes novos devem reaproveitar a estrutura e o CSS dos quizzes já existentes (perguntas em `.question-block` com `data-q` e `data-correct`, feedback visual nas opções, explicação expansível e placar no final) para manter a consistência visual.

Ver `CLAUDE.md` para as regras completas do projeto.

## Rodar localmente

O site precisa de um servidor — abrir `index.html` com `file://` direto não funciona, porque o `fetch('manifest.json')` é bloqueado.

```bash
python3 -m http.server 8123
```

```bash
npx serve .
```

Depois abra `http://localhost:8123` (ou a porta que o comando indicar).

### Pelo Claude Code

O repositório traz um `.claude/launch.json` já configurado com um servidor chamado **`site`** na porta 8123. Basta pedir ao Claude Code para rodar o preview do projeto — ele sobe esse servidor e abre o site no painel do navegador, sem precisar do comando manual.

## Deploy

O repositório está conectado ao Vercel como projeto estático. Cada push na branch principal gera um deploy novo automaticamente.
