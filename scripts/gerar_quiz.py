#!/usr/bin/env python3
"""
Gera um quiz interativo no padrão do projeto a partir de um JSON de conteúdo.

    python3 scripts/gerar_quiz.py conteudo/meu_quiz.json

O JSON carrega só o conteúdo; toda a estrutura (CSS, telas, placar, script de
pontuação) sai daqui. Assim vários quizzes saem estruturalmente idênticos, que é
o que o CLAUDE.md e o DIRETRIZES_QUIZ.md exigem.

Formato do JSON — ver scripts/exemplo_quiz.json para um exemplo completo:

{
  "arquivo":   "materias/ciencias/quiz_ciencias_2026_tri2_x_completa_v1.html",
  "title":     "título da aba",
  "h1":        "🧬 TÍTULO NA TELA",
  "subtitulo": "5º Ano • 2º Trimestre • ...",
  "badge":     "🔬 Missão: ...",
  "nota":      "texto em itálico no fim da introdução (aceita HTML)",
  "topicos":   [ {"titulo": "...", "texto": "..."} ],
  "fases": [
    {
      "titulo": "⚡ FASE 1: ...",
      "desc":   "linha em itálico sob o título da fase",
      "texto_apoio": "opcional — bloco de leitura válido para a fase inteira",
      "questoes": [
        {
          "tag":   "rótulo curto da questão",
          "texto": "enunciado (sem o número; ele é gerado)",
          "texto_apoio": "opcional — bloco de leitura só desta questão",
          "svg":   "opcional — <svg>...</svg> inline, para tirinha ou diagrama",
          "correta": "B",
          "alts": [ {"l": "A", "t": "texto da alternativa", "e": "explicação"} ]
        }
      ]
    }
  ]
}

Regras que o script garante sozinho:
  - numeração sequencial das questões, atravessando as fases;
  - prefixo "✅ Correto!" ou "❌ Incorreto." em cada explicação;
  - STORAGE_KEY e totalQuestions coerentes com o arquivo e a contagem real.

E recusa gerar se: o gabarito apontar para letra inexistente, houver letra
repetida, ou alguma alternativa ficar sem explicação.
"""
import json
import sys
from pathlib import Path

CSS = """        :root {
            --bg-color: #0f172a;
            --container-bg: #1e293b;
            --accent-color: #38bdf8;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --correct-bg: #16a34a;
            --incorrect-bg: #dc2626;
            --border-color: #334155;
            --tooltip-bg: #0f172a;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            -webkit-tap-highlight-color: transparent;
        }
        .quiz-container {
            width: 100%;
            max-width: 700px;
            background-color: var(--container-bg);
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        .screen { display: none; }
        .screen.active { display: block; }
        h1 { color: var(--accent-color); text-align: center; font-size: 26px; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; cursor: pointer; user-select: none; }
        h1:hover { opacity: 0.9; }
        .subtitle { text-align: center; color: var(--text-muted); font-size: 14px; margin-bottom: 30px; }
        .intro-box { background-color: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 12px; padding: 25px; margin-bottom: 30px; }
        .theme-badge { display: inline-block; background-color: rgba(56, 189, 248, 0.15); color: var(--accent-color); border: 1px solid var(--accent-color); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 15px; }
        .intro-title { font-size: 18px; color: var(--accent-color); margin-top: 0; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
        .topic-group { margin-bottom: 20px; }
        .topic-group h3 { font-size: 16px; margin: 0 0 5px 0; color: #ffffff; }
        .topic-group p { font-size: 14px; color: var(--text-muted); margin: 0; }
        .intro-note { font-size: 13px; color: var(--text-muted); font-style: italic; margin-top: 20px; }
        .phase-title { background-color: var(--border-color); padding: 10px 15px; border-radius: 8px; font-size: 16px; font-weight: bold; margin-top: 30px; margin-bottom: 15px; border-left: 4px solid var(--accent-color); }
        .phase-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 20px; font-style: italic; }
        .question-block { background-color: rgba(255, 255, 255, 0.02); padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 1px solid var(--border-color); }
        .question-tag { display: inline-block; background-color: var(--border-color); color: var(--accent-color); padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 10px; }
        .question-text { font-size: 16px; font-weight: 500; margin-bottom: 15px; line-height: 1.5; }
        .text-box-analysis { background-color: rgba(56, 189, 248, 0.08); border-left: 4px solid var(--accent-color); padding: 15px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; line-height: 1.6; }
        .comic-strip { background-color: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; padding: 8px; margin-bottom: 15px; }
        .comic-strip svg { display: block; width: 100%; height: auto; }
        .options-container { display: flex; flex-direction: column; gap: 12px; }
        .option-clickable { background-color: rgba(255, 255, 255, 0.05); border: 1px solid var(--border-color); color: var(--text-color); padding: 14px 16px; border-radius: 8px; font-size: 14px; display: flex; justify-content: space-between; align-items: center; gap: 10px; box-sizing: border-box; cursor: pointer !important; user-select: none; }
        .option-clickable * { pointer-events: none !important; }
        .feedback-badge { display: none; font-size: 16px; flex-shrink: 0; }
        .explanation-box { display: none; margin-top: 8px; padding: 11px 15px; background-color: var(--tooltip-bg); border-left: 3px solid var(--accent-color); border-radius: 4px; font-size: 13px; line-height: 1.45; }
        .option-clickable.correct { background-color: var(--correct-bg) !important; border-color: var(--correct-bg) !important; color: #ffffff !important; }
        .option-clickable.correct .badge-correct { display: inline-block !important; }
        .option-clickable.incorrect { background-color: var(--incorrect-bg) !important; border-color: var(--incorrect-bg) !important; color: #ffffff !important; }
        .option-clickable.incorrect .badge-incorrect { display: inline-block !important; }
        .option-clickable.hint-green { border: 2px dashed #16a34a !important; background-color: rgba(22, 163, 74, 0.1) !important; }
        .option-clickable.hint-green .badge-hint { display: inline-block !important; }
        .score-banner { margin-top: 30px; padding: 20px; background-color: rgba(56, 189, 248, 0.1); border: 2px dashed var(--accent-color); border-radius: 12px; text-align: center; }
        .score-text { font-size: 20px; font-weight: bold; color: var(--accent-color); margin-bottom: 15px; }
        .action-btn { background-color: var(--accent-color); color: var(--bg-color); border: none; padding: 14px 28px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer !important; display: inline-block; text-align: center; user-select: none; }
        .center-btn-wrapper { display: flex; justify-content: center; width: 100%; }"""

JS = """<script>
    (function() {
        let score = 0;
        let answeredQuestions = {};
        let wrongAnswers = [];
        const totalQuestions = __TOTAL__;
        const STORAGE_KEY = 'estudoKevin:scores:__ARQUIVO__';
        const screenIntro = document.getElementById('screen-intro');
        const screenQuiz = document.getElementById('screen-quiz');
        const btnStart = document.getElementById('btn-start-quiz');
        const btnFinish = document.getElementById('btn-finish-quiz');
        const mainTitle = document.getElementById('main-title');

        function showScreen(screenToShow) {
            screenIntro.classList.remove('active');
            screenQuiz.classList.remove('active');
            screenToShow.classList.add('active');
            window.scrollTo(0, 0);
        }

        if (btnStart) {
            btnStart.addEventListener('click', function(e) {
                e.preventDefault();
                showScreen(screenQuiz);
            });
        }

        if (mainTitle) {
            mainTitle.addEventListener('click', function(e) {
                e.preventDefault();
                showScreen(screenIntro);
            });
        }

        function handleResponse(element) {
            const block = element.closest('.question-block');
            if (!block) return;
            const qNum = block.getAttribute('data-q');
            const correctAnswer = block.getAttribute('data-correct');
            const selectedLetter = element.getAttribute('data-letter');
            if (answeredQuestions[qNum]) return;
            answeredQuestions[qNum] = selectedLetter;
            const parentContainer = block.querySelector('.options-container');
            const wrappers = parentContainer.children;
            for (let i = 0; i < wrappers.length; i++) {
                const opt = wrappers[i].querySelector('.option-clickable');
                const expBox = wrappers[i].querySelector('.explanation-box');
                const optLetter = opt.getAttribute('data-letter');
                if (selectedLetter === correctAnswer) {
                    if (optLetter === correctAnswer) opt.classList.add('correct');
                } else {
                    if (opt === element) opt.classList.add('incorrect');
                    else if (optLetter === correctAnswer) opt.classList.add('hint-green');
                }
                if (expBox) expBox.style.display = 'block';
            }
            if (selectedLetter === correctAnswer) {
                score++;
            } else {
                const correctEl = block.querySelector(`.option-clickable[data-letter="${correctAnswer}"]`);
                wrongAnswers.push({
                    q: qNum,
                    text: block.querySelector('.question-text').textContent.trim(),
                    chosen: element.querySelector('span').textContent.trim(),
                    correct: correctEl ? correctEl.querySelector('span').textContent.trim() : correctAnswer
                });
            }
            document.getElementById('score-display').textContent = `Pontuação: ${score} / ${totalQuestions}`;
            if (Object.keys(answeredQuestions).length === totalQuestions) {
                try {
                    const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
                    history.push({ score, total: totalQuestions, date: new Date().toISOString(), wrong: wrongAnswers });
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
                } catch(e) {}
            }
        }

        document.querySelectorAll('.option-clickable').forEach(el => {
            el.addEventListener('click', function(e) {
                e.preventDefault();
                handleResponse(this);
            });
        });

        if (btnFinish) {
            btnFinish.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = '/';
            });
        }
    })();
</script>"""

BADGES = ('<span class="feedback-badge badge-correct">✅</span>'
          '<span class="feedback-badge badge-incorrect">❌</span>'
          '<span class="feedback-badge badge-hint">💡</span>')


def validar(cfg):
    """Recusa gerar um quiz quebrado. Devolve a lista de problemas."""
    problemas = []
    n = 0
    for fase in cfg["fases"]:
        for q in fase["questoes"]:
            n += 1
            letras = [a["l"] for a in q["alts"]]
            if q["correta"] not in letras:
                problemas.append(f'q{n}: gabarito "{q["correta"]}" não existe entre {letras}')
            if len(set(letras)) != len(letras):
                problemas.append(f"q{n}: letra repetida em {letras}")
            for a in q["alts"]:
                if not a.get("e", "").strip():
                    problemas.append(f'q{n} alternativa {a["l"]}: sem explicação')
    if n == 0:
        problemas.append("nenhuma questão no JSON")
    return problemas


def gerar(cfg):
    total = sum(len(f["questoes"]) for f in cfg["fases"])
    out = []
    a = out.append

    a('<!DOCTYPE html>')
    a('<html lang="pt-BR">')
    a('<head>')
    a('    <meta charset="UTF-8">')
    a('    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">')
    a(f'    <title>{cfg["title"]}</title>')
    a('    <style>')
    a(CSS)
    a('    </style>')
    a('</head>')
    a('<body>')
    a('<div class="quiz-container">')
    a(f'    <h1 id="main-title">{cfg["h1"]}</h1>')
    a(f'    <div class="subtitle">{cfg["subtitulo"]}</div>')
    a('')
    a('    <div id="screen-intro" class="screen active">')
    a('        <div class="intro-box">')
    if cfg.get("badge"):
        a(f'            <span class="theme-badge">{cfg["badge"]}</span>')
    a('            <h2 class="intro-title">📋 Conteúdos Mapeados na Missão:</h2>')
    for t in cfg["topicos"]:
        a('            <div class="topic-group">')
        a(f'                <h3>{t["titulo"]}</h3>')
        a(f'                <p><b>Tópicos:</b> {t["texto"]}</p>')
        a('            </div>')
    if cfg.get("nota"):
        a(f'            <div class="intro-note">{cfg["nota"]}</div>')
    a('        </div>')
    a('        <div class="center-btn-wrapper">')
    a('            <div class="action-btn" id="btn-start-quiz" onclick="">Iniciar Missão</div>')
    a('        </div>')
    a('    </div>')
    a('')
    a('    <div id="screen-quiz" class="screen">')

    n = 0
    for fase in cfg["fases"]:
        a('')
        a(f'        <div class="phase-title">{fase["titulo"]}</div>')
        a(f'        <div class="phase-desc">{fase["desc"]}</div>')
        if fase.get("texto_apoio"):
            a('')
            a(f'        <div class="text-box-analysis">{fase["texto_apoio"]}</div>')

        for q in fase["questoes"]:
            n += 1
            a('')
            a(f'        <div class="question-block" data-q="{n}" data-correct="{q["correta"]}">')
            if q.get("tag"):
                a(f'            <span class="question-tag">{q["tag"]}</span>')
            a(f'            <div class="question-text">{n}. {q["texto"]}</div>')
            if q.get("texto_apoio"):
                a(f'            <div class="text-box-analysis">{q["texto_apoio"]}</div>')
            if q.get("svg"):
                a('            <div class="comic-strip">')
                a(f'                {q["svg"].strip()}')
                a('            </div>')
            a('            <div class="options-container">')
            for o in q["alts"]:
                marca = '✅ Correto!' if o["l"] == q["correta"] else '❌ Incorreto.'
                a('                <div>')
                a(f'                    <div class="option-clickable" data-letter="{o["l"]}" onclick="">'
                  f'<span>({o["l"]}) {o["t"]}</span>{BADGES}</div>')
                a(f'                    <div class="explanation-box">{marca} {o["e"]}</div>')
                a('                </div>')
            a('            </div>')
            a('        </div>')

    a('')
    a('        <div class="score-banner">')
    a(f'            <div class="score-text" id="score-display">Pontuação: 0 / {total}</div>')
    a('            <div class="action-btn" id="btn-finish-quiz" onclick="">Terminar Missão</div>')
    a('        </div>')
    a('    </div>')
    a('</div>')
    a(JS.replace('__TOTAL__', str(total)).replace('__ARQUIVO__', cfg["arquivo"]))
    a('</body>')
    a('</html>')
    return '\n'.join(out) + '\n'


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 64
    cfg = json.load(open(sys.argv[1], encoding='utf-8'))

    problemas = validar(cfg)
    if problemas:
        print("não gerei — corrija o JSON primeiro:")
        for p in problemas:
            print("  •", p)
        return 1

    saida = Path(sys.argv[2] if len(sys.argv) > 2 else cfg["arquivo"])
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(gerar(cfg), encoding='utf-8')

    total = sum(len(f["questoes"]) for f in cfg["fases"])
    alts = sum(len(q["alts"]) for f in cfg["fases"] for q in f["questoes"])
    textos = sum(1 for f in cfg["fases"] if f.get("texto_apoio")) + \
             sum(1 for f in cfg["fases"] for q in f["questoes"] if q.get("texto_apoio"))
    svgs = sum(1 for f in cfg["fases"] for q in f["questoes"] if q.get("svg"))
    print(f"gerado {saida}")
    print(f"  {total} questões · {len(cfg['fases'])} fases · {alts} explicações "
          f"· {textos} texto(s) de apoio · {svgs} svg(s)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
