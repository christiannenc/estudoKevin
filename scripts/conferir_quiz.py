#!/usr/bin/env python3
"""
Confere um quiz contra o contrato do projeto, sem precisar abrir o navegador.

    python3 scripts/conferir_quiz.py materias/ciencias/quiz_*.html
    python3 scripts/conferir_quiz.py materias/*/quiz_*.html

Verifica:
  - nome do arquivo na convenção;
  - IDs que o script do quiz exige;
  - totalQuestions coerente com o número de blocos de questão;
  - data-q em sequência de 1 a N;
  - data-correct apontando para uma alternativa existente, sem letra repetida;
  - cobertura das explicações (por alternativa é o padrão; por questão é exceção);
  - STORAGE_KEY batendo com o caminho do próprio arquivo;
  - ausência de recurso externo e de markdown vazado;
  - botão final voltando para a home.

Sai com código 1 se algum arquivo tiver erro, para servir em verificação automática.
"""
import re
import sys
from pathlib import Path

CONVENCAO = re.compile(
    r'^([a-z]+)_([a-z]+)_(\d{4})_tri(\d)_.+_(parcial|completa)_v(\d+)\.html$', re.I)

IDS = ['main-title', 'screen-intro', 'screen-quiz',
       'btn-start-quiz', 'btn-finish-quiz', 'score-display']


def universais(html, p):
    """Checagens que valem para qualquer quiz, novo ou legado.

    "Autocontido" quer dizer sem buscar nada na rede. Imagem versionada ao lado
    do HTML conta como parte do exercício: o site publica os dois juntos. O que
    não pode é src remoto (quebra sem internet) nem caminho absoluto (quebra ao
    mudar a pasta). Arquivo local que não existe também é erro: link quebrado.
    """
    erros = []
    if re.search(r'<link[^>]+rel="stylesheet"', html):
        erros.append('folha de estilo externa — o CSS do quiz fica no próprio arquivo')

    for src in re.findall(r'<(?:img|script)[^>]+src="([^"]*)"', html):
        if src.startswith('data:'):
            continue
        if re.match(r'(?:[a-z]+:)?//|/', src):
            erros.append(f'recurso fora do repositório: "{src}" — o quiz deve funcionar sem rede')
        elif not (p.parent / src).exists():
            erros.append(f'arquivo referenciado não existe: "{src}"')
    return erros


def blocos(html):
    """Fatia o HTML em blocos de questão."""
    partes = re.split(r'<div class="question-block"', html)[1:]
    for p in partes:
        cabeca = p.split('>', 1)[0]
        q = re.search(r'data-q="(\d+)"', cabeca)
        c = re.search(r'data-correct="([A-Z])"', cabeca)
        corpo = re.split(r'<div class="score-banner"', p)[0]
        yield (q.group(1) if q else None,
               c.group(1) if c else None,
               re.findall(r'data-letter="([A-Z])"', corpo),
               corpo.count('class="explanation-box"'))


def conferir(caminho):
    p = Path(caminho)
    html = p.read_text(encoding='utf-8')
    erros, avisos = [], []

    if not CONVENCAO.match(p.name):
        erros.append('nome fora da convenção {tipo}_{materia}_{ano}_tri{N}_..._{parcial|completa}_v{N}.html')

    # Alguns quizzes são anteriores ao padrão atual: funcionam no site, mas usam
    # outra marcação. Não faz sentido listar 20 erros estruturais neles — basta
    # sinalizar que são legado e checar só o que vale para qualquer arquivo.
    if 'data-letter="' not in html:
        n_blocos = html.count('class="question-block"')
        avisos.append('LEGADO — marcação anterior ao padrão atual. Funciona, mas não serve '
                      'de modelo para quiz novo e não dá para verificar em detalhe.')
        erros += universais(html, p)
        return erros, avisos, n_blocos

    faltando = [i for i in IDS if f'id="{i}"' not in html]
    if faltando:
        erros.append('IDs ausentes: ' + ', '.join(faltando))

    qs = list(blocos(html))
    if not qs:
        erros.append('nenhum bloco .question-block encontrado')
        return erros, avisos, 0

    nums = [int(n) for n, _, _, _ in qs if n]
    if nums != list(range(1, len(qs) + 1)):
        erros.append(f'data-q fora de sequência: {nums}')

    m = re.search(r'const totalQuestions = (\d+);', html)
    if not m:
        erros.append('totalQuestions não encontrado no script')
    elif int(m.group(1)) != len(qs):
        erros.append(f'totalQuestions={m.group(1)} mas há {len(qs)} questões')

    total_alts = 0
    total_exp = 0
    for n, correta, letras, n_exp in qs:
        total_alts += len(letras)
        total_exp += n_exp
        if not letras:
            erros.append(f'q{n}: sem alternativas com data-letter')
            continue
        if correta is None:
            erros.append(f'q{n}: sem data-correct')
        elif correta not in letras:
            erros.append(f'q{n}: gabarito "{correta}" não existe entre {letras}')
        if len(set(letras)) != len(letras):
            erros.append(f'q{n}: letra repetida em {letras}')

    if total_exp == 0:
        erros.append('nenhuma explicação no arquivo')
    elif total_exp < total_alts:
        avisos.append(f'explicação por questão ({total_exp} para {total_alts} alternativas) — '
                      'o padrão é uma por alternativa')

    chave = re.search(r"STORAGE_KEY = 'estudoKevin:scores:([^']+)'", html)
    if not chave:
        erros.append('STORAGE_KEY não encontrada')
    elif chave.group(1) != str(p).replace('\\', '/'):
        erros.append(f'STORAGE_KEY aponta para "{chave.group(1)}", mas o arquivo é "{p}"')

    erros += universais(html, p)

    md = re.findall(r'\*\*[^*\n]+\*\*', html)
    if md:
        avisos.append(f'markdown vazado: {md[:3]}')

    if "window.location.href = '/'" not in html:
        avisos.append('o botão final não volta para a home')

    return erros, avisos, len(qs)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 64

    houve_erro = False
    for caminho in sys.argv[1:]:
        erros, avisos, n = conferir(caminho)
        nome = Path(caminho).name
        legado = any(a.startswith('LEGADO') for a in avisos)
        marca = '✗' if erros else ('~' if legado else '✓')
        print(f'{marca} {nome} ({n} questões)')
        if erros:
            houve_erro = True
        for e in dict.fromkeys(erros):          # sem repetir a mesma linha
            print('    ERRO   ', e)
        for a in avisos:
            print('    aviso  ', a)
    return 1 if houve_erro else 0


if __name__ == '__main__':
    sys.exit(main())
