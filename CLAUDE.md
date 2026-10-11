# Ajudando o Kevin a estudar

Site estático com exercícios de estudo (quizzes HTML interativos e folhas para imprimir em PDF) organizados por matéria, para apoiar os estudos do filho do usuário (apelido do projeto: Kevin).

## Stack

HTML/CSS/JS puro, sem build step, sem framework. Hospedado no Vercel como projeto estático (deploy automático a cada push no GitHub).

## Estrutura

```
index.html              → página inicial (lista as matérias em acordeão)
manifest.json            → fonte de dados: lista de exercícios por matéria
assets/
  style.css              → estilo compartilhado (tema escuro)
  mascote.png             → mascote do site, também usado como favicon
  mascote.svg             → mascote desenhado da versão anterior, fora de uso
materias/
  {materia}/
    {arquivo}.html ou .pdf  → os exercícios em si
```

## Convenção de nome de arquivo (IMPORTANTE)

Todo exercício segue este padrão, e o `index.html` faz parsing automático do nome para gerar o título exibido:

```
{tipo}_{materia}_{ano}_tri{N}_{descricao_livre}_{parcial|completa}_v{N}.{html|pdf}
```

Exemplo: `quiz_portugues_2026_tri2_prova_parcial_v1.html`

- `tipo`: **usado no parsing.** `quiz` = quiz interativo com pontuação; qualquer outro valor (`impressao`, `exercicio`, `redacao`, etc.) = material de impressão
- `materia`: bate com a chave da matéria no manifest.json
- `ano`: ano letivo
- `tri{N}`: trimestre (tri1, tri2, tri3)
- `descricao_livre`: qualquer coisa, não entra no título gerado
- `parcial` ou `completa`: indica se é uma versão reduzida ou completa do conteúdo
- `v{N}`: número da versão

**Regra de versão: cada versão é um exercício SEPARADO, não substitui a anterior.** v1 e v2 do mesmo trimestre/completude aparecem como dois cards distintos na lista. O título gerado sempre inclui o tipo e a versão para diferenciá-los (ex: "Quiz · 2º trimestre 2026 · Parcial · v1"). O rótulo do tipo vem do mapa `TIPO_LABEL` no `index.html` — tipo novo que não estiver lá cai num fallback que só capitaliza a primeira letra, então vale acrescentar ao mapa.

**O `tipo` decide o badge; a extensão decide como o link abre.** São duas regras separadas — folha de impressão também pode ser `.html`:

- `tipo` = `quiz` (e extensão `.html`) → badge "Quiz", grava pontuação, mostra histórico
- qualquer outro `tipo` → badge "Imprimir", sem placar e sem a linha "Ainda não feito"
- extensão `.html` → abre em nova aba (`target="_blank"`); `.pdf` → abre na mesma aba

A função `ehQuiz(info)` no `index.html` centraliza essa decisão — usar sempre ela em vez de testar a extensão.

## Fluxo normal de trabalho (toda vez que o usuário pedir para adicionar um exercício novo)

1. Salvar o arquivo em `materias/{materia}/` seguindo a convenção de nome acima. Se a matéria ainda não existe na pasta nem no manifest, criar ambos.
2. Adicionar uma entrada nova no array `exercicios` da matéria correspondente em `manifest.json`, com:
   - `"arquivo"`: caminho relativo a partir da raiz do projeto (ex: `"materias/portugues/quiz_portugues_2026_tri2_prova_parcial_v2.html"`)
   - `"assunto"`: um resumo curto e legível dos assuntos/tópicos cobertos no exercício (isso é digitado manualmente, não vem do nome do arquivo — geralmente está na primeira página/pergunta do material)
3. Não editar manualmente o título exibido em nenhum lugar — ele é sempre gerado pelo JS do `index.html` a partir do nome do arquivo.
4. Commit e push. Se o repositório estiver conectado ao Vercel, o deploy é automático.

## Quizzes HTML — padrão de implementação

Os quizzes seguem o padrão do `quiz_portugues_2026_tri2_prova_parcial_v1.html`: tema escuro, perguntas em `.question-block` com `data-q` e `data-correct`, alternativas em `.option-clickable` com `data-letter`, feedback visual (verde = correto, vermelho = incorreto, verde tracejado na certa quando o aluno erra) e, no fim, o `.score-banner` com o botão **"Terminar Missão"**, que devolve o aluno para a home (`window.location.href = '/'`). **Não existe botão de reiniciar** — cada passada é uma tentativa nova no histórico.

**Explicação por alternativa é o padrão.** Cada `.option-clickable` tem a sua `.explanation-box` irmã, e a da alternativa errada aponta a confusão específica daquela opção, em vez de repetir a justificativa da correta. Só quando o volume for inviável ou o conteúdo ficar complexo demais é aceitável cair para uma explicação por questão — é o caso dos dois quizzes abrangentes de Português, por decisão do usuário. Não "corrigir" esses dois sem pedido.

Dois arquivos anteriores a esse padrão (`quiz_ciencias_2026_tri2_prova_parcial_v1.html` e `quiz_histgeo_2026_tri2_prova_parcial_v3.html`) usam outros nomes de classe. Funcionam, mas não servem de modelo.

As regras de **conteúdo pedagógico** (temática, distribuição das questões, tela de introdução, gabarito da versão de impressão, recomendações técnicas de JS) ficam em `DIRETRIZES_QUIZ.md` — é o prompt que o usuário cola na IA que gera o material. Consultar esse arquivo ao criar um quiz do zero.

## Mascote (`assets/mascote.png`)

- Imagem escolhida pelo usuário: menino de óculos escrevendo num caderno. Gerada por IA a pedido dele, recortada com o Vision do macOS e enquadrada do peito para cima.
- PNG quadrado de 512×512 com fundo transparente. Exibido a 64px no cabeçalho e usado também como favicon — por isso precisa ser quadrado, senão a imagem achata.
- `assets/mascote.svg` é um mascote desenhado à mão, da versão anterior. Fica como reserva e **não está em uso**.
- **Não usar imagens ou personagens com direitos autorais de terceiros** (ex: Minions). O site é publicado na internet, o que descarta a hipótese de uso privado.

Ao trocar a imagem: recortar o fundo, enquadrar do peito para cima (corpo inteiro fica ilegível a 64px), exportar PNG quadrado com transparência e conferir como fica a 32px, que é o tamanho do favicon.

## Histórico de pontuação dos quizzes

O `index.html` deve exibir, em cada card de quiz, o histórico de pontuação de tentativas anteriores e indicar visualmente se o quiz já foi feito ou não. Regras:

- Usar `localStorage` **somente** para armazenar o histórico de pontuação dos quizzes. Chave: `estudoKevin:scores:` + o caminho do arquivo a partir da raiz do projeto, igual ao campo `arquivo` do manifest. Valor: array de `{score, total, date, wrong}`, em que `wrong` lista os erros da tentativa como `{q, text, chosen, correct}` — **é esse campo que alimenta o modal de revisão da home**, então não pode ser omitido. Esta é a única exceção ao "não usar localStorage".
- Card não feito: visual neutro/padrão
- Card já feito: exibir a última pontuação e badge de "Feito" (ou similar)
- O histórico detalhado pode ser exibido em tooltip ou expansão no card

## Ordenação e agrupamento dos cards de exercício

Dentro de cada matéria, a ordem é **curricular e fixa** — não depende de o quiz já ter sido feito. Critérios, nesta sequência (função `sortKey` no `index.html`):

1. **Ano decrescente** — mais recente primeiro
2. **Trimestre decrescente** — mais recente primeiro
3. **Completa antes de parcial** — a prova abrangente é a mais recente do trimestre
4. **Quiz antes do material impresso** — o aluno treina no quiz e depois faz a folha
5. **Versão decrescente** — v3 antes de v2 antes de v1

Os cards são agrupados em **dois níveis** pelo `renderMateria`:

- `.trimestre-sep` — quando o ano/trimestre muda (ex: "2º trimestre 2026"). Arquivo fora da convenção de nome cai no bloco "Outros materiais", no fim da lista.
- `.completude-sep` — dentro do trimestre, quando muda de completa para parcial (rótulos "Conteúdo completo" e "Conteúdo parcial"). O rótulo se repete no início de cada trimestre novo; arquivo fora da convenção não recebe subtítulo.

**O histórico de pontuação não entra na ordenação.** O badge "Ainda não feito" e a lista de tentativas continuam no card, mas fazer um quiz não muda a posição dele — a lista precisa ser estável e previsível.

## O que NÃO fazer

- Não usar localStorage/sessionStorage para nada além do histórico de pontuação dos quizzes.
- Não adicionar build step, framework ou dependências de pacote sem necessidade — o ponto forte deste projeto é a simplicidade de só soltar um arquivo HTML/PDF novo e atualizar o manifest.
- Não usar imagens ou personagens com direitos autorais de terceiros (ex: Minions). O site é publicado na internet, o que afasta a hipótese de uso privado — a regra vale mesmo quando o pedido parte do usuário.
