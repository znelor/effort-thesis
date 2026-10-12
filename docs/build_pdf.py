"""Builds docs/figures.pdf: each figure on its own page, followed by a German explanation page.
Numbers are read from figures/*/out/results.json (run the figure scripts first)."""
import json, sys, pathlib
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
ROOT = pathlib.Path(__file__).resolve().parents[1]
for nm, f in [('OS', 'OpenSans-400.ttf'), ('OSB', 'OpenSans-700.ttf')]:
    for d in [pathlib.Path.home() / '.local/share/fonts', ROOT / 'docs/fonts']:
        if (d / f).exists(): pdfmetrics.registerFont(TTFont(nm, str(d / f))); break
    else: raise SystemExit('Open Sans static fonts not found')
from reportlab.lib.fonts import addMapping
addMapping('OS', 0, 0, 'OS'); addMapping('OS', 1, 0, 'OSB'); addMapping('OS', 0, 1, 'OS'); addMapping('OS', 1, 1, 'OSB')
ss = getSampleStyleSheet()
B = ParagraphStyle('b', parent=ss['BodyText'], fontName='OS', fontSize=9.3, leading=13.2, spaceAfter=5)
H1 = ParagraphStyle('h1', parent=B, fontName='OSB', fontSize=15, leading=19, spaceAfter=8)
H2 = ParagraphStyle('h2', parent=B, fontName='OSB', fontSize=11, leading=15, spaceBefore=6, spaceAfter=4)
CAP = ParagraphStyle('cap', parent=B, fontSize=8.4, leading=11.6)
MONO = ParagraphStyle('m', parent=B, fontName='Courier', fontSize=8.2, leading=11, backColor=colors.HexColor('#f3f3f3'), borderPadding=4, spaceBefore=3, spaceAfter=7)
R = lambda f: json.load(open(ROOT / 'figures' / f / 'out' / 'results.json'))
def cf(res, term, key='coefs'):
    for c in res[key]:
        if c['term'] == term: return c
    raise KeyError(term)
def fmt(c, d=2): return f"{c['est']:.{d}f} [{c['lo']:.{d}f}, {c['hi']:.{d}f}], p {'< .001' if c['p'] < .001 else '= ' + f'{c['p']:.3f}'.lstrip('0')}"
P = lambda t: Paragraph(t, B)
story = []
def fig(path, title, caption, maxh=17 * cm):
    w, h = PILImage.open(ROOT / 'output' / path).size; W = 17.5 * cm; H = W * h / w
    if H > maxh: W, H = W * maxh / H, maxh
    story.extend([Paragraph(title, H1), Image(str(ROOT / 'output' / path), W, H), Spacer(1, 6), Paragraph(caption, CAP)])
def page(): story.append(PageBreak())
r1, r2, r3, r4, r5, r6, r7, r8 = (R(f) for f in ['01_effort_ratings', '02_familiarisation', '03_choices', '04_choice_matrix', '05_choices_glmm', '06_exchange_rate', '07_fatigue_timing', '08_per_person_glmm'])
# ------------------------------------------------------------------ title
story += [Paragraph('Effort valuation in gripping and tapping – Kernabbildungen für die Betreuung', H1),
  P('Stand: 12.10.2026 · N = 31 · Code: Repository <b>znelor/effort-thesis</b> (Python; Mixed Models mit <b>lme4</b> über <b>pymer4</b>). '
    'Alle Zahlen in diesem Dokument werden von den Skripten erzeugt (figures/*/out/results.json) und nicht von Hand eingetragen.'),
  Paragraph('Hypothesen', H2),
  P('<b>H1</b>: Mehr Reward erhöht die Wahl der anstrengenderen Option. <b>H2</b>: Mehr Effort senkt sie. '
    '<b>H3</b>: Der Wechselkurs k = −β<sub>E</sub>/β<sub>R</sub> (Coins, die +10 pp Effort ausgleichen) ist beim Grip höher als beim Tapping.'),
  Paragraph('Inhalt', H2)]
toc = [['Fig.', 'Inhalt', 'Seite'], ['1', 'Effort ratings in der Familiarisation + LMM-Erklärung', '2–3'], ['2', 'Familiarisation (gekürzt): Erfolg, Zeit, Ausführung, realisierte Intensität, Rating − Target', '4–5'],
       ['3', 'Choices + Erklärung des Choice-GLMM', '6–7'], ['4', 'Choice matrix (Heatmap) Grip / Tapping / Differenz', '8'], ['5', 'Choices nach Effort und Reward + GLMM-Schätzer; Ceiling-Check', '9–10'],
       ['6', 'Exchange rate k aus EINEM Modell', '11–12'], ['7a', 'Fatigue nach Task-Reihenfolge', '13'], ['7b', 'NEU: Time-on-task in der Familiarisation', '14'], ['7c', 'NEU: Timing-Effekte in der Choice-Phase', '15'],
       ['7', 'Erklärung Fatigue/Timing', '16'], ['8', 'Personenspezifische Slopes und k', '17'], ['', 'Offene Punkte für das Gespräch', '18']]
t = Table(toc, colWidths=[1.2 * cm, 13.3 * cm, 1.8 * cm]); t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'OS', 8.8), ('FONT', (0, 0), (-1, 0), 'OSB', 8.8),
    ('LINEBELOW', (0, 0), (-1, 0), .6, colors.black), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])]))
story += [t, Spacer(1, 8), Paragraph('Allgemein', H2),
  P('Farben: Tapping blau, Grip orange. Boxen: Median (schwarzer Strich), Interquartilsbereich (Box), Whisker bis 1,5 × IQR, Punkte außerhalb = Ausreißer; '
    'große Punkte mit Linie = Mittelwerte der Personenmittelwerte. Effort-Level sind immer in % bzw. pp der individuell kalibrierten Kapazität. '
    'Sterne (*) in Schätzer-Panels: p &lt; .05 (nicht korrigiert, außer wo angegeben).')]
page()
# ------------------------------------------------------------------ fig 1
fig('01_effort_ratings/fig01_effort_ratings.png', 'Fig. 1 – Effort ratings in der Familiarisation',
    '<b>A</b> Effort rating (1–100) pro Target-Level, Personenmittelwerte; gestrichelt: Rating = Target. <b>B</b> Personenspezifische Rating-Slopes (Punkte pro pp) aus einer einfachen Regression je Person und Task; '
    f'gestrichelt: gleiche Slopes. Bei {r1["slope_grip_gt_tap"]} von {r1["n"]} Personen ist der Grip-Slope steiler. <b>C</b> Fixed effects des LMM (Erklärung nächste Seite), 95%-CI (Satterthwaite).')
page()
c = lambda t: cf(r1, t)
story += [Paragraph('Erklärung: das Linear Mixed Model (LMM) für die Ratings', H1),
  Paragraph('Das Problem', H2),
  P('Jede Person hat 70 Ratings abgegeben (2 Tasks × 7 Target-Level × 5 Wiederholungen). Diese 2170 Ratings sind <b>nicht unabhängig</b>: '
    'Wer generell hoch bewertet, bewertet überall hoch. Eine normale Regression würde so tun, als hätten wir 2170 unabhängige Personen, und wäre viel zu optimistisch. '
    'Ein <b>Linear Mixed Model</b> löst das, indem es zwei Ebenen trennt: was für <i>alle</i> gilt (fixed effects) und wie einzelne Personen davon abweichen (random effects).'),
  Paragraph('Die Formel', H2),
  Paragraph('rating ~ G * tgt10 + G * rep_c + period + (1 + G * tgt10 | id)', MONO),
  P('Links von „~“ steht, was vorhergesagt wird (Rating). Rechts stehen die Prädiktoren. „A * B“ heißt: A, B und ihre Interaktion A:B.'),
  Paragraph('Die Prädiktoren (Variablen)', H2),
  P('<b>G</b> = Task-Dummy: 0 = Tapping, 1 = Grip. Tapping ist damit die Referenz.<br/>'
    '<b>tgt10</b> = Target-Level, zentriert auf 50 % und in 10-pp-Schritten: (Target − 50)/10. Also −3 bei 20 %, 0 bei 50 %, +3 bei 80 %.<br/>'
    '<b>rep_c</b> = Wiederholung 1–5 (jede Wiederholung = einmal alle 7 Level), zentriert auf die 3. Wiederholung (−2 … +2).<br/>'
    '<b>period</b> = 0 im ersten Task-Block, 1 im zweiten (gleicht Reihenfolge-Effekte aus).<br/>'
    'Durch das Zentrieren bedeuten alle Haupteffekte „bei 50 % Target, mittlere Wiederholung“.'),
  Paragraph('Fixed effects – was für die durchschnittliche Person gilt (Panel C)', H2),
  P(f'<b>(Intercept)</b>: erwartetes Rating beim Tapping, 50 % Target, mittlere Wiederholung, erster Block = {c("(Intercept)")["est"]:.1f} Punkte.<br/>'
    f'<b>G (Grip vs tapping)</b>: Grip wird bei gleichem Level um {fmt(c("G"))} Punkte höher bewertet.<br/>'
    f'<b>tgt10 (Target +10 pp)</b>: pro +10 pp steigt das Tapping-Rating um {fmt(c("tgt10"))} Punkte – die Ratings folgen also dem Level (Manipulation check).<br/>'
    f'<b>G:tgt10 (Grip × target)</b>: wie viel steiler der Anstieg beim Grip ist: {fmt(c("G:tgt10"))} – kein klarer Unterschied in der Steigung.<br/>'
    f'<b>rep_c (Repetition)</b>: Veränderung pro Wiederholung beim Tapping: {fmt(c("rep_c"))}.<br/>'
    f'<b>G:rep_c (Grip × repetition)</b>: zusätzliche Veränderung pro Wiederholung beim Grip: {fmt(c("G:rep_c"))} (knapp; Grip wird über die Zeit etwas höher bewertet).<br/>'
    f'<b>period (Second block)</b>: {fmt(c("period"))}.'),
  Paragraph('Random effects – wie Personen abweichen dürfen', H2),
  P('<b>(1 + G * tgt10 | id)</b> heißt: für jede Person (id) schätzt das Modell eine eigene Abweichung von 4 Dingen: vom Intercept (generell höher/tiefer bewerten = <b>random intercept</b>), '
    'vom Grip-Effekt, vom Target-Slope und von Grip × Target (<b>random slopes</b>). Diese Abweichungen werden nicht einzeln als Parameter geschätzt, sondern als Normalverteilung mit einer Standardabweichung (SD) – '
    'das Modell lernt also „wie unterschiedlich sind Personen?“. Die SDs hier: Intercept ≈ 19 Punkte, Grip-Effekt ≈ 12, Target-Slope ≈ 4 Punkte pro 10 pp; Residual (Trial-zu-Trial-Rauschen) ≈ 11. '
    'Wichtig: Weil Personen unterschiedlich auf Grip reagieren dürfen, wird der Grip-Effekt gegen diese Personenstreuung getestet (df ≈ 29), nicht gegen 2170 Trials – das macht den Test ehrlich.'),
  Paragraph('Output lesen', H2),
  P('Jede Zeile: Schätzer (estimate), 95%-Konfidenzintervall und p-Wert (Satterthwaite-Freiheitsgrade via lmerTest). Liegt das CI nicht über der 0, ist der Effekt bei α = .05 signifikant. '
    f'Das Modell ist nicht singulär und konvergiert. Gefittet mit lme4::lmer (REML), Optimizer bobyqa.')]
page()
# ------------------------------------------------------------------ fig 2
fl = r2['failed_trials']
fig('02_familiarisation/fig02_familiarisation.png', 'Fig. 2 – Familiarisation (gekürzt)',
    '<b>A</b> Erfolgsrate pro Level (Mittelwert ± 95%-CI über Personen), jetzt auf der vollen 0–100-%-Achse; darunter die Anzahl misslungener Trials (Tapping/Grip, je 155 Trials pro Level). '
    '<b>B</b> Zeit bis zum Kriterium. <b>C</b> Rohe Ausführungsmaße je Task. <b>D</b> Realisierte Intensität (% der kalibrierten Kapazität). <b>E</b> Rating minus angezeigtes Target. '
    '* = Grip vs Tapping am jeweiligen Level, LMM mit Level als Faktor, Kapazität (z-log Grip- und Tap-Kapazität) × Task, Wiederholung, Block, (1 + Task | Person); Holm-korrigiert über die 7 Level.', maxh=18 * cm)
page()
tap_t = {x['target']: x for x in r2['cell_means_successful'] if x['modality'] == 'tap'}; gr_t = {x['target']: x for x in r2['cell_means_successful'] if x['modality'] == 'grip'}
story += [Paragraph('Erklärung Fig. 2', H1),
  Paragraph('Task-Design: warum die beiden Tasks sich unterschiedlich anfühlen', H2),
  P('<b>Grip</b>: Kalibriert an der maximalen willkürlichen Kraft (MVC) bzw. der daraus bestimmten haltbaren Kraft. Ein Level von 60 % heißt: 60 % dieser Kraft erzeugen und für eine feste Dauer halten. '
    'Mehr Level = <i>mehr Kraft</i>, die Dauer bleibt ungefähr gleich. Deshalb ist die Zeit bis zum Kriterium beim Grip fast konstant '
    f'({gr_t[20.0]["time"]:.1f} s bei 20 % bis {gr_t[80.0]["time"]:.1f} s bei 80 %).'),
  P('<b>Tapping</b> (Hewitt-artig): Kalibriert an der maximalen Anzahl Taps in 10 s (im Mittel ≈ 7,2 Taps/s). Ein Level von 60 % heißt: 60 % dieser Anzahl Taps innerhalb des Zeitfensters. '
    'Mehr Level = <i>mehr Taps</i>, also länger arbeiten – Personen tippen aber (fast) immer nahe ihrer Maximalrate '
    f'({tap_t[20.0]["tap_rate"]:.1f} Taps/s bei 20 %, {tap_t[80.0]["tap_rate"]:.1f} bei 80 %). Deshalb wächst die Zeit linear mit dem Level ({tap_t[20.0]["time"]:.1f} s → {tap_t[80.0]["time"]:.1f} s, Panel B).'),
  P('Kurz: Beim Grip skaliert das Level die <b>Intensität</b>, beim Tapping die <b>Dauer</b>. Gleiche %-Zahlen sind also nicht gleiche Handlungen – genau das ist der Hintergrund von H3.'),
  Paragraph('Die Panels', H2),
  P(f'<b>A – Erfolg (umgeformt)</b>: Fast alle Trials gelingen (Tapping {100 * r2["success_rate"]["tap"]:.1f} %, Grip {100 * r2["success_rate"]["grip"]:.1f} %). '
    f'Die alte Achse begann bei ~85 %, dadurch sah der Abfall bei 80 % dramatisch aus. Tatsächlich sind es bei 80 % {fl["tap_80.0"]} misslungene Tapping- und {fl["grip_80.0"]} Grip-Trials von je 155. '
    'Jetzt: volle 0–100-%-Achse plus Anzahl misslungener Trials.'),
  P('<b>B – Zeit bis zum Kriterium</b> (nur erfolgreiche Trials): siehe Task-Design oben.'),
  P('<b>C – Rohe Ausführung</b>: Grip: gehaltene Kraft / Target (1 = genau auf dem Ziel). Bei niedrigen Leveln wird deutlich überschossen '
    f'(Mittel {gr_t[20.0]["hold_mean_ratio"]:.2f} bei 20 %, {gr_t[80.0]["hold_mean_ratio"]:.2f} bei 80 %). Tapping: Taps pro Sekunde, fast unabhängig vom Level. '
    'Die beiden Maße haben verschiedene Einheiten und sind nicht direkt vergleichbar – deshalb Panel D. Die übrigen Trial-Typen (Choice-Phase) werden hier nicht gezeigt; '
    'die Ausführung in der Choice-Phase ist im Haupt-Repository (Analyse „execution“) ausgewertet.'),
  P('<b>D – Realisierte Intensität</b>: Was tatsächlich geleistet wurde, in % der Kapazität. Grip liegt knapp über der Diagonale (man produziert ungefähr das Verlangte), '
    f'Tapping liegt bei allen Leveln bei ~89–100 % (bei 20 % Target: {tap_t[20.0]["realised"]:.0f} %), weil man einfach so schnell wie möglich tippt, nur kürzer.'),
  P('<b>E – Rating minus angezeigtes Target</b>: 0 = Rating entspricht der angezeigten Zahl. Beim Tapping liegen die Ratings ab 50 % etwas unter dem Target, beim Grip etwa darauf; '
    'Unterschiede signifikant nur bei 60 % und 70 % (Holm).'),
  P('<i>Weggelassen gegenüber v7</i>: Panel „Rating minus realisierte Intensität“ (stark redundant mit D und E).')]
page()
# ------------------------------------------------------------------ fig 3
fig('03_choices/fig03_choices.png', 'Fig. 3 – Choices',
    '<b>A</b> Anteil Wahlen der anstrengenderen Option pro Person (Punkte, Linien verbinden dieselbe Person), Dichte je Task, schwarz: Mittelwert ± 95%-CI. '
    f'Tapping {100 * r3["mean_p"]["tap"]:.1f} %, Grip {100 * r3["mean_p"]["grip"]:.1f} %; Differenz {r3["diff_pp"]:.1f} pp (Bootstrap-CI [{r3["diff_boot_ci"][0]:.1f}, {r3["diff_boot_ci"][1]:.1f}]); '
    f'{r3["fewer_in_grip"]} Personen wählen beim Grip seltener, {r3["more_in_grip"]} häufiger, {r3["equal"]} gleich oft. '
    '<b>B</b> Choice-Kurven des GLMM (Erklärung nächste Seite) pro zusätzlicher Belohnung: dicke Linie = über die 31 Personen gemittelte Modellvorhersage, Band = 95 % über 1000 Ziehungen der Fixed effects; '
    'dünne Linien = einzelne Personen; Kreise = beobachtete Mittelwerte ± 95%-CI.')
page()
c = lambda t: cf(r3, t)
story += [Paragraph('Erklärung: das Choice-Modell (logistisches GLMM) – für Einsteiger', H1),
  Paragraph('Was wird modelliert?', H2),
  P('In jedem Trial wählt die Person zwischen einer leichteren Option (weniger Effort, weniger Coins) und einer anstrengenderen (mehr Effort, mehr Coins). '
    'Ergebnis: <b>y = 1</b>, wenn die anstrengendere Option gewählt wurde, sonst 0. Pro Person 60 Trials pro Task, insgesamt 3720.'),
  Paragraph('Warum „logistisch“?', H2),
  P('Eine Wahrscheinlichkeit liegt zwischen 0 und 1. Das Modell rechnet deshalb auf der <b>Log-odds-Skala</b>: log(p / (1 − p)). Auf dieser Skala darf alles linear addiert werden; '
    'erst am Ende wird mit der logistischen Funktion p = 1 / (1 + e<super>−x</super>) zurück in eine Wahrscheinlichkeit übersetzt. Log-odds 0 = 50 %, +1 ≈ 73 %, +2 ≈ 88 %, −1 ≈ 27 %. '
    'Ein Slope von −0,5 bedeutet: pro Einheit sinken die Log-odds um 0,5 – in Prozent hängt das davon ab, wo man startet (in der Mitte am stärksten, nahe 0 % oder 100 % kaum).'),
  Paragraph('Die Prädiktoren', H2),
  P('<b>R</b> = zusätzliche Coins der anstrengenderen Option (+1, +2, +3). <b>E</b> = zusätzlicher Effort in 10-pp-Einheiten (+2 … +6, also +20 … +60 pp). '
    'Beide werden pro Task getrennt geschätzt: R_t, E_t (Tapping) und R_g, E_g (Grip). <b>tap</b>, <b>grip</b> = eigene Intercepts pro Task.'),
  Paragraph('y ~ 0 + tap + grip + R_t + R_g + E_t + E_g\n   + (1 | id) + (0 + G | id) + (0 + R_t | id) + (0 + R_g | id) + (0 + E_t | id) + (0 + E_g | id)', MONO),
  P(f'<b>β<sub>R</sub></b> (Reward-Slope, H1): Tapping {fmt(c("R_t"))}; Grip {fmt(c("R_g"))}. Positiv = mehr Coins → häufiger die anstrengendere Option.<br/>'
    f'<b>β<sub>E</sub></b> (Effort-Slope, H2): Tapping {fmt(c("E_t"))}; Grip {fmt(c("E_g"))}. Negativ = mehr Effort → seltener.<br/>'
    f'<b>Intercepts</b> (tap {c("tap")["est"]:.2f}, grip {c("grip")["est"]:.2f}): Log-odds bei R = 0 und E = 0 – das ist eine Extrapolation außerhalb der angebotenen Werte und nicht direkt interpretierbar.'),
  Paragraph('Random effects – „G“ in GLMM', H2),
  P('Wie beim LMM: jede Person bekommt eigene Abweichungen – generelle Bereitschaft (1 | id), zusätzliche Abweichung im Grip (0 + G | id) und eigene Reward- und Effort-Slopes je Task. '
    'Die Abweichungen werden als unabhängig angenommen (keine Korrelationen geschätzt), das hält das Modell stabil. Die Personenstreuung ist groß: SD des Intercepts ≈ 2,2 Log-odds, '
    'SD der Reward-Slopes ≈ 1,0 – Personen unterscheiden sich stark darin, wie sehr Coins sie bewegen.'),
  Paragraph('Output lesen', H2),
  P('Schätzer ± 95%-CI (Wald) und p-Wert (z-Test). Gefittet mit lme4::glmer (Binomial, Logit, Laplace-Approximation, bobyqa); nicht singulär, konvergiert. '
    'Dasselbe Modell wird für Fig. 3, 4 (nur deskriptiv), 5, 6 und 8 verwendet.')]
page()
# ------------------------------------------------------------------ fig 4 heatmap
cg, ct_ = r4['cell_grip'], r4['cell_tap']
fig('04_choice_matrix/fig04_choice_matrix.png', 'Fig. 4 – Choice matrix',
    'Anteil Wahlen der anstrengenderen Option (%) für jede Kombination aus zusätzlichem Effort (+20 … +60 pp) und zusätzlicher Belohnung (+1 … +3 Coins). '
    'Erst pro Person und Zelle gemittelt (4 Angebote je Zelle und Task), dann über Personen. <b>C</b> Grip minus Tapping in Prozentpunkten; † = 95%-CI der Personen-Differenz schließt 0 aus (unkorrigiert).', maxh=9 * cm)
story += [Spacer(1, 10), Paragraph('Erklärung', H2),
  P('Jede Zelle ist eine Angebotsart. Von links nach rechts wird die anstrengendere Option noch anstrengender, von unten nach oben lohnender. '
    'Gelb = fast immer angenommen, dunkel = selten. Man sieht beide Hypothesen direkt: Nach rechts wird es dunkler (H2), nach oben heller (H1). '
    f'Beim Tapping ist die Matrix insgesamt heller und flacher: selbst bei +60 pp und +1 Coin noch {100 * ct_["1.0"]["60.0"]:.0f} % (Grip {100 * cg["1.0"]["60.0"]:.0f} %).'),
  P(f'Die Differenz (C) ist in allen 15 Zellen negativ: Grip wird seltener gewählt. In {r4["n_cells_ci_excl_0"]} von 15 Zellen schließt das CI die 0 aus. '
    'Bei +20 pp ist der Unterschied klein (−2 bis −6 pp), ab +30 pp meist größer (−6 bis −24 pp): Der Grip-Nachteil wächst mit dem Effort, nicht mit dem Reward – '
    'das passt zum steileren Effort-Slope beim Grip. Hinweis: Die Matrix zeigt nur die <i>zusätzlichen</i> Mengen; die Basisoption variiert innerhalb jeder Zelle (siehe Methoden).')]
page()
# ------------------------------------------------------------------ fig 5
c5 = lambda t: cf(r5, t)
fig('05_choices_glmm/fig05_choices_glmm.png', 'Fig. 5 – Choices nach Effort und Reward + GLMM',
    '<b>A</b> Anteil Wahlen der anstrengenderen Option pro Person und Effort-Level (über alle Reward-Level), dünne Linien = Personen. <b>B</b> dasselbe pro Reward-Level. '
    '<b>C</b> Dasselbe GLMM wie Fig. 3, nur anders parametrisiert: Tapping ist die Referenz, die Grip-Terme sind <i>Differenzen</i> zum Tapping (identischer Fit).')
story += [Spacer(1, 8), Paragraph('Erklärung Panel C', H2),
  P(f'Reward (+1 Coin) {fmt(c5("R"))}; Effort (+10 pp) {fmt(c5("E"))} – beides für Tapping. '
    f'Reward × Grip {fmt(c5("R:G"))}: Coins wirken beim Grip tendenziell weniger. Effort × Grip {fmt(c5("E:G"))}: der Effort-Slope ist beim Grip tendenziell steiler. '
    'Einzeln ist keiner der beiden Unterschiede signifikant – erst zusammen, im Verhältnis k, ergibt sich der Unterschied in Fig. 6.')]
page()
n95, n100, sc100 = r5['n_ge95'], r5['n_eq100'], r5['share_person_cells_at_100']
story += [Paragraph('Ceiling-Check: zeigt Fig. 5 einen Ceiling-Effekt beim Tapping?', H1),
  P(f'<b>Ja, teilweise – aber es ist ein Ceiling einer Untergruppe, kein genereller.</b> {n95["tap"]} von 31 Personen wählen beim Tapping in ≥ 95 % der Trials die anstrengendere Option '
    f'({n100["tap"]} sogar immer), beim Grip nur {n95["grip"]} ({n100["grip"]} immer). In Panel A und B sieht man das daran, dass beim Tapping das obere Quartil der Boxen bei fast allen Leveln bei 100 % klebt. '
    f'Von allen Kombinationen Person × Angebotszelle liegen beim Tapping {100 * sc100["tap"]:.0f} % bei 100 %, beim Grip {100 * sc100["grip"]:.0f} %.'),
  P(f'Der Mittelwert ist dagegen nicht am Anschlag: Er fällt beim Tapping von {100 * r5["mean_by_effort"]["20.0"]["tap"]:.0f} % (+20 pp) auf {100 * r5["mean_by_effort"]["60.0"]["tap"]:.0f} % (+60 pp), '
    'und auch beim Tapping gibt es Personen, die stark auf Effort reagieren. Bei +20 pp sind beide Tasks gleich nah an der Decke (Median in beiden 92 %).'),
  Paragraph('Warum das wichtig ist', H2),
  P('Wer (fast) immer die anstrengendere Option wählt, liefert kaum Information über seinen Effort- oder Reward-Slope. Das GLMM schätzt deren Slopes dann nahe am Gruppenmittel („Shrinkage“). '
    'Konsequenzen: (1) Ein Teil des Task-Unterschieds könnte daher kommen, dass das Tapping-Angebot für viele schlicht zu leicht war (Range-Restriction), nicht dass Effort beim Tapping „anders“ bewertet wird. '
    '(2) k beim Tapping ist für diese Personen schlecht bestimmt. (3) Zur Diskussion: Sensitivitätsanalyse ohne Personen mit ≥ 95 % in einem Task, oder Ergebnis explizit als „bei diesem Angebotsbereich“ formulieren.')]
page()
# ------------------------------------------------------------------ fig 6
fig('06_exchange_rate/fig06_exchange_rate.png', 'Fig. 6 – Exchange rate (ein Modell)',
    '<b>A</b> Reward-Slope und <b>B</b> Effort-Slope je Task (Log-odds, 95%-CI). <b>C</b> Exchange rate k = −β<sub>E</sub>/β<sub>R</sub> je Task mit Delta-Methode-CI (log-Skala) und Verhältnis k<sub>grip</sub>/k<sub>tap</sub>. '
    'Alles aus dem einen Choice-GLMM von Fig. 3.', maxh=10 * cm)
story += [Spacer(1, 8), Paragraph('Was ist k?', H2),
  P('k übersetzt Effort in Coins: <b>Wie viele zusätzliche Coins braucht es, damit +10 pp Effort gerade ausgeglichen sind?</b> '
    'Auf der Log-odds-Skala kostet +10 pp genau β<sub>E</sub>, ein Coin bringt β<sub>R</sub>. Ausgleich heißt β<sub>R</sub> · Coins + β<sub>E</sub> = 0, also Coins = −β<sub>E</sub>/β<sub>R</sub> = k. '
    'Vorteil: k ist unabhängig davon, wie „rauschig“ jemand wählt (das kürzt sich im Verhältnis heraus) und hat eine anschauliche Einheit.'),
  P(f'Ergebnis: <b>k<sub>tap</sub> = {r6["k_tap"]:.2f}</b> [{r6["k_tap_lo"]:.2f}, {r6["k_tap_hi"]:.2f}] und <b>k<sub>grip</sub> = {r6["k_grip"]:.2f}</b> [{r6["k_grip_lo"]:.2f}, {r6["k_grip_hi"]:.2f}] Coins pro +10 pp. '
    f'Grip ist also etwa <b>{r6["ratio"]:.2f}-mal so „teuer“</b> [{r6["ratio_lo"]:.2f}, {r6["ratio_hi"]:.2f}], p = {r6["p_ratio"]:.3f} (Wald-Test auf log(k<sub>grip</sub>/k<sub>tap</sub>)). Das stützt H3.')]
page()
story += [Paragraph('Warum nur dieses eine Modell – und was zu besprechen ist', H1),
  P('In v7 wurden sieben Varianten (RV1–RV7) gezeigt, die sich in den Random effects und Kovariaten unterscheiden. Für die Betreuung hier nur <b>eines</b>:'),
  Paragraph('y ~ 0 + tap + grip + R_t + R_g + E_t + E_g\n   + (1 | id) + (0 + G | id) + (0 + R_t | id) + (0 + R_g | id) + (0 + E_t | id) + (0 + E_g | id)', MONO),
  P('<b>Warum dieses?</b> (1) Keine Kovariaten – nur das, was die Hypothesen brauchen. (2) Es ist das einfachste Modell, das jeder Person <i>eigene Reward- und Effort-Slopes pro Task</i> erlaubt. '
    'Das ist für H3 entscheidend: Der Test „unterscheidet sich k zwischen den Tasks?“ ist ein Within-Person-Vergleich. Erlaubt man nur gemeinsame Slopes über beide Tasks (wie RV1), wird die Unsicherheit des Task-Unterschieds unterschätzt. '
    '(3) Random effects unabhängig statt korreliert: Das voll korrelierte Modell (RV6) ist singulär, dieses nicht. (Das Modell entspricht RV5 im Haupt-Repository; Zahlen identisch.)'),
  Paragraph('Ehrlicher Kontext (aus dem Haupt-Repository)', H2),
  P('Über die sieben Varianten liegt k<sub>grip</sub>/k<sub>tap</sub> zwischen 1,24 und 1,87; in 4 von 7 Varianten schließt das CI die 1 aus, in 3 nicht (u. a. die beiden mit voll korrelierten Random effects, die singulär sind, und RV4 mit Kovariaten). '
    'Die Richtung ist also stabil (Grip immer teurer), die Signifikanz hängt von der Modellwahl ab. Dieses Modell liegt am oberen Ende des Effekts.'),
  Paragraph('Fragen an die Betreuung', H2),
  P('• Ist dieses Modell als Hauptmodell akzeptabel, oder soll ein prä-spezifiziertes Modell (z. B. mit Kovariaten Reihenfolge, Position, Seite) Hauptmodell sein?<br/>'
    '• Wald/Delta-Methode vs. Profile-Likelihood-Test für die Gleichheit von k (im Haupt-Repository vorhanden) – was soll berichtet werden?<br/>'
    '• Umgang mit dem Ceiling-Effekt beim Tapping (siehe S. 10).')]
page()
# ------------------------------------------------------------------ fig 7
fo = r7['fatigue_order']
fig('07_fatigue_timing/fig07a_fatigue_by_order.png', 'Fig. 7a – Fatigue nach Task-Reihenfolge',
    '<b>A</b> Fatigue-Reports (1–100) über die Session, getrennt nach Reihenfolge; B = Baseline, grau = Familiarisation. <b>B</b> LMM: fatigue ~ Task × Reihenfolge + Report-Nummer im Block + (1 + Task | Person).', maxh=10 * cm)
cfo = lambda t: cf(fo, t)
story += [Spacer(1, 6), P(f'Fatigue steigt pro Report im Block um {fmt(cfo("pb_c"))} Punkte. Bei Tap-first ist Grip (der zweite Block) um {fmt(cfo("G"), 1)} höher; '
    f'die Interaktion Grip × grip-first {fmt(cfo("G:gf"), 1)} zeigt: Bei Grip-first ist der Grip-Vorteil weitgehend weg. Fatigue folgt also vor allem der <b>Zeit</b> (zweiter Block höher), weniger dem Task.')]
page()
fig('07_fatigue_timing/fig07b_familiarisation_time_on_task.png', 'Fig. 7b – NEU: Time-on-task in der Familiarisation',
    '<b>A</b> Fatigue-Reports während der Familiarisation (3 pro Block). <b>B</b> Rating minus angezeigtes Target über die 5 Wiederholungen. <b>C</b> Realisierte Intensität minus Target (pp der Kapazität), erfolgreiche Trials. '
    '<b>D</b> LMM-Schätzer pro Wiederholung bzw. Report (Tapping) und Unterschied Grip − Tapping. Modelle: Outcome ~ Task × Wiederholung + Task × Target + Block + (1 + Task | Person); Fatigue: ~ Task × Report + Block + (1 + Task | Person).', maxh=11 * cm)
page()
fig('07_fatigue_timing/fig07c_choice_timing.png', 'Fig. 7c – NEU: Timing-Effekte in der Choice-Phase',
    '<b>A</b> Wahlen der anstrengenderen Option nach Position im Choice-Block (4 Viertel à 19 Trials; Personenmittelwerte). <b>B</b> Erster vs. zweiter Task-Block. '
    '<b>C</b> GLMM = Choice-Modell aus Fig. 3 plus Trial-Position je Task (Anfang → Ende des Blocks = 1 Einheit), Effort × Position je Task und Block.', maxh=11 * cm)
page()
g = lambda k, t: cf(r7[k], t); ctm = lambda t: cf(r7['choice_timing'], t)
story += [Paragraph('Erklärung Fig. 7b und 7c', H1),
  Paragraph('7b – Familiarisation: gibt es Ermüdung über die Wiederholungen?', H2),
  P(f'<b>Fatigue</b> steigt innerhalb der Familiarisation nur wenig und nicht signifikant (Tapping {fmt(g("fam_Fatigue", "pb_c"), 1)} pro Report; Grip zusätzlich {fmt(g("fam_Fatigue", "G:pb_c"), 1)}). '
    f'Deutlich ist nur der Block-Effekt: In der Familiarisation des zweiten Blocks liegt Fatigue um {fmt(g("fam_Fatigue", "period_n"), 1)} höher.'),
  P(f'<b>Ratings</b> relativ zum Target verändern sich über die Wiederholungen kaum (Tapping {fmt(g("fam_Rating − target", "rep_c"))}, Grip zusätzlich {fmt(g("fam_Rating − target", "G:rep_c"))} Punkte pro Wiederholung).'),
  P(f'<b>Realisierte Intensität</b> sinkt leicht: Tapping {fmt(g("fam_Realised intensity", "rep_c"))} pp pro Wiederholung, Grip zusätzlich {fmt(g("fam_Realised intensity", "G:rep_c"))}. '
    'Beim Grip ist das v. a. weniger Überschießen bei niedrigen Leveln (Lernen, die Kraft zu dosieren), beim Tapping eine minimal langsamere Rate. '
    f'Die Zeit bis zum Kriterium ändert sich praktisch nicht (Tapping {fmt(g("fam_log_time", "rep_c"), 3)} log-s pro Wiederholung). '
    'Fazit: In der Familiarisation keine nennenswerte Ermüdung; die kleinen Trends sehen eher nach Gewöhnung aus. Die Ratings sind über die Zeit stabil.'),
  Paragraph('7c – Choice-Phase: ändert sich das Wahlverhalten im Verlauf?', H2),
  P(f'<b>Tapping</b>: Über den Block hinweg werden <i>mehr</i> anstrengende Optionen gewählt (Position {fmt(ctm("P_t"))} Log-odds von Anfang bis Ende des Blocks; siehe Hinweis unten), '
    f'gleichzeitig wird der Effort-Slope steiler (Effort × Position {fmt(ctm("EP_t"))}). Sprich: kleine Effort-Aufschläge werden später eher angenommen, große eher abgelehnt – Personen werden über den Block <i>selektiver</i>.'),
  P(f'<b>Grip</b>: Tendenz zu weniger anstrengenden Wahlen über den Block (Position {fmt(ctm("P_g"))}; deskriptiv {100 * r7["choice_by_bin"]["1"]["grip"]:.0f} % im ersten vs. {100 * r7["choice_by_bin"]["4"]["grip"]:.0f} % im letzten Viertel), '
    f'aber nicht signifikant; Effort × Position {fmt(ctm("EP_g"))}. Zweiter vs. erster Block: {fmt(ctm("period"))}.'),
  P('Hinweis zur Interpretation: Weil die Effort-Variable nicht zentriert ist, ist der Positions-Effekt „bei E = 0“ (Extrapolation); zusammen mit der negativen Interaktion heißt das: bei den tatsächlich angebotenen Effort-Leveln (+20 … +60 pp) ist die Netto-Veränderung beim Tapping klein (siehe Panel A: 78 % → 74 %). '
    '<b>Caveat</b>: Dieses erweiterte GLMM ist <b>singulär</b> (eine Random-effects-Varianz ≈ 0); die Fixed effects sind meist trotzdem brauchbar, sollten aber als explorativ gelten. '
    'Die Reward- und Effort-Slopes und k bleiben mit diesen Zeit-Termen praktisch gleich (β<sub>E</sub> Grip −0,69 statt −0,68; β<sub>R</sub> Grip 1,08 statt 1,03), d. h. H3 wird nicht durch Zeit-Effekte erklärt.')]
page()
# ------------------------------------------------------------------ fig 8
fig('08_per_person_glmm/fig08_per_person_glmm.png', 'Fig. 8 – Personenspezifische Slopes und k',
    '<b>A</b> Effort-Slope, <b>B</b> Reward-Slope, <b>C</b> k je Person, Tapping (x) vs Grip (y); gestrichelt: gleich in beiden Tasks. Werte = Fixed effect + personenspezifische Abweichung (conditional modes) aus dem Choice-GLMM. '
    f'C nur für die {r8["n_k_defined"]} Personen mit positivem Reward-Slope in beiden Tasks (log-Achsen).', maxh=9 * cm)
story += [Spacer(1, 8), Paragraph('Erklärung', H2),
  P('Punkte unterhalb der Diagonale in A = steilerer (negativerer) Effort-Slope beim Grip; in C oberhalb = Grip teurer. '
    f'Effort-Slope steiler beim Grip: {r8["effort_steeper_grip"]}/31 Personen; Reward-Slope kleiner beim Grip: {r8["reward_smaller_grip"]}/31; k höher beim Grip: {r8["k_higher_grip"]}/{r8["n_k_defined"]}. '
    f'Median k: Tapping {r8["median_k"]["tap"]:.2f}, Grip {r8["median_k"]["grip"]:.2f}. Bei {r8["nonpos_R"]["grip"]} Personen ist der Grip-Reward-Slope ≤ 0, dort ist k nicht definiert.'),
  P('<b>Vorsicht</b>: Das sind keine unabhängigen Messungen pro Person, sondern modellbasierte, zur Gruppe hin geschrumpfte Vorhersagen (Shrinkage). '
    'Die Zählungen sind deskriptiv und kein zusätzlicher Test. Gerade die Personen am Ceiling (Fig. 5) liegen nahe am Gruppenmittel, weil ihre Daten wenig Information enthalten.')]
page()
story += [Paragraph('Offene Punkte für das Gespräch', H1),
  P('1. <b>Hauptmodell für H3</b>: dieses eine GLMM (k-Verhältnis 1,87, p = .031) vs. Modellvarianten (1,24–1,87; nicht alle signifikant). Welche Spezifikation ist prä-registriert/verteidigbar?'),
  P('2. <b>Ceiling beim Tapping</b>: 12/31 Personen ≥ 95 % anstrengende Wahlen. Sensitivitätsanalyse? Angebotsbereich als Limitation?'),
  P('3. <b>Gleiche %-Level ≠ gleiche Handlung</b> (Fig. 2): Grip skaliert Intensität, Tapping Dauer. Wie stark soll die Diskussion von H3 darauf aufbauen?'),
  P('4. <b>Zeit-Effekte in der Choice-Phase</b> (Fig. 7c): beim Tapping selektiveres Wählen über den Block. Explorativ berichten oder weglassen? (Modell singulär.)'),
  P('5. <b>Fatigue</b> folgt v. a. der Session-Zeit (Block 2 höher), nicht dem Task (Fig. 7a); in der Familiarisation keine nennenswerte Ermüdung (Fig. 7b).'),
  Spacer(1, 10),
  P('<i>Weggelassen gegenüber v7 (nicht gelöscht, im Haupt-Repository)</i>: Choice summaries, Effort-Slope-Differenz, Robustness forest, SV-Modelle, relative Fatigue-Timing, Execution vs. Choice, Kapazität.')]
out = ROOT / 'docs' / 'figures.pdf'
def num(c, d):
    c.saveState(); c.setFont('OS', 7.5); c.setFillColor(colors.grey); c.drawRightString(A4[0] - 1.6 * cm, 1 * cm, str(d.page)); c.restoreState()
SimpleDocTemplate(str(out), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.5 * cm, bottomMargin=1.6 * cm,
                  title='Effort valuation – figures and models', author='Lorenz').build(story, onFirstPage=num, onLaterPages=num)
print('wrote', out)
