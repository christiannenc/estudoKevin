# Ajudando o Kevin a estudar

Site simples com exercícios de estudo para o Kevin: quizzes interativos e folhas para imprimir, organizados por matéria.

## Rodar localmente

Não tem build nem dependências — é só HTML/CSS/JS estático. Abra `index.html` com um servidor local (não funciona com `file://` direto por causa do `fetch('manifest.json')`). Exemplos:

```bash
npx serve .
# ou
python3 -m http.server 8000
```

## Deploy

Conectar este repositório ao Vercel como projeto estático. Cada push na branch principal gera um deploy novo automaticamente.

## Como adicionar um exercício novo

Ver `CLAUDE.md` para o passo a passo detalhado e a convenção de nome de arquivo. Resumo rápido:

1. Salvar o arquivo em `materias/{materia}/` com o nome no formato `{tipo}_{materia}_{ano}_tri{N}_{descricao}_{parcial|completa}_v{N}.{html|pdf}`.
2. Adicionar uma entrada em `manifest.json` com o caminho do arquivo e um resumo do assunto.
3. Commit e push.
