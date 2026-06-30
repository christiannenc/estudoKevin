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
  mascote.svg             → mascote original do site (não usar IP de terceiros aqui)
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

- `tipo`: livre (quiz, prova, redacao, etc.) — não é usado no parsing, só organizacional
- `materia`: bate com a chave da matéria no manifest.json
- `ano`: ano letivo
- `tri{N}`: trimestre (tri1, tri2, tri3)
- `descricao_livre`: qualquer coisa, não entra no título gerado
- `parcial` ou `completa`: indica se é uma versão reduzida ou completa do conteúdo
- `v{N}`: número da versão

**Regra de versão: cada versão é um exercício SEPARADO, não substitui a anterior.** v1 e v2 do mesmo trimestre/completude aparecem como dois cards distintos na lista. O título gerado sempre inclui a versão para diferenciá-los (ex: "2º trimestre 2026 · Parcial · v1").

A extensão do arquivo decide o badge e o comportamento do link:
- `.html` → badge "Quiz", abre em nova aba (`target="_blank"`)
- `.pdf` → badge "Imprimir", abre na mesma aba

## Fluxo normal de trabalho (toda vez que o usuário pedir para adicionar um exercício novo)

1. Salvar o arquivo em `materias/{materia}/` seguindo a convenção de nome acima. Se a matéria ainda não existe na pasta nem no manifest, criar ambos.
2. Adicionar uma entrada nova no array `exercicios` da matéria correspondente em `manifest.json`, com:
   - `"arquivo"`: caminho relativo a partir da raiz do projeto (ex: `"materias/portugues/quiz_portugues_2026_tri2_prova_parcial_v2.html"`)
   - `"assunto"`: um resumo curto e legível dos assuntos/tópicos cobertos no exercício (isso é digitado manualmente, não vem do nome do arquivo — geralmente está na primeira página/pergunta do material)
3. Não editar manualmente o título exibido em nenhum lugar — ele é sempre gerado pelo JS do `index.html` a partir do nome do arquivo.
4. Commit e push. Se o repositório estiver conectado ao Vercel, o deploy é automático.

## Quizzes HTML — padrão de implementação

Os quizzes seguem o estilo do arquivo já existente em `materias/portugues/`: tema escuro, perguntas em `.question-block` com `data-q` e `data-correct`, opções clicáveis com feedback visual (verde = correto, vermelho = incorreto, dica em verde tracejado na opção certa quando o usuário erra), explicação que expande abaixo da opção respondida, e placar no final com botão de reiniciar. Ao criar um quiz novo, reaproveitar essa estrutura/CSS para manter consistência visual entre os exercícios.

## Mascote (`assets/mascote.svg`)

- Desenho original, sem IP de terceiros
- Design definido: boneco com **dois olhos** e **segurando uma banana**
- Ao editar ou recriar o mascote, manter essas características

## Histórico de pontuação dos quizzes

O `index.html` deve exibir, em cada card de quiz, o histórico de pontuação de tentativas anteriores e indicar visualmente se o quiz já foi feito ou não. Regras:

- Usar `localStorage` **somente** para armazenar o histórico de pontuação dos quizzes (chave: nome do arquivo, valor: array de `{score, total, date}`). Esta é a única exceção ao "não usar localStorage".
- Card não feito: visual neutro/padrão
- Card já feito: exibir a última pontuação e badge de "Feito" (ou similar)
- O histórico detalhado pode ser exibido em tooltip ou expansão no card

## Ordenação dos cards de exercício

Dentro de cada matéria, os cards devem ser ordenados por:
1. **Não feitos primeiro** (quizzes sem histórico no localStorage aparecem antes dos feitos)
2. **Mais recentes primeiro** (desempate pelo ano + trimestre + versão, do maior para o menor)

PDFs (sem histórico possível) são sempre tratados como "não feitos" para fins de ordenação.

## O que NÃO fazer

- Não usar localStorage/sessionStorage para nada além do histórico de pontuação dos quizzes.
- Não adicionar build step, framework ou dependências de pacote sem necessidade — o ponto forte deste projeto é a simplicidade de só soltar um arquivo HTML/PDF novo e atualizar o manifest.
- Não usar imagens ou personagens com direitos autorais de terceiros (ex: Minions) — o mascote do site é um desenho original.
