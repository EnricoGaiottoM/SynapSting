"""Gera os anexos dos e-mails a partir de docs/contato.json:
  docs/resumo_1pagina.pdf           -> para laboratórios (pedido de apoio)
  docs/resumo_revisor_2paginas.pdf  -> para quem vai revisar o modelo
Uso: python docs/make_figure_resumo.py && python docs/make_summaries.py
"""
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
                                KeepTogether, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", D + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", D + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", D + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVB")
C = json.load(open("docs/contato.json"))
AZUL, CINZA, LARANJA = colors.HexColor("#1d3557"), colors.HexColor("#5c677d"), colors.HexColor("#d17a22")

def S(name, size=8.6, lead=11.2, font="DV", color=colors.black, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=lead, textColor=color, **kw)
TIT = S("t", 19, 22, "DVB", AZUL); SUB = S("s", 9.5, 12.5, "DV", CINZA)
H = S("h", 9.6, 12, "DVB", AZUL, spaceBefore=5, spaceAfter=1.5)
B = S("b", 8.6, 11.2); BUL = S("bl", 8.6, 11.2, leftIndent=9, bulletIndent=0)
B2 = S("b2", 8.6, 12.6); BUL2 = S("bl2", 8.6, 12.6, leftIndent=9, bulletIndent=0)
SM = S("sm", 7.2, 9, "DV", CINZA); CAP = S("cap", 7.4, 9.2, "DVI", CINZA)

def bullets(items, st=None):
    return [Paragraph(t, st or BUL, bulletText="•") for t in items]

def box(flow, bg="#fff4e8", border=LARANJA):
    t = Table([[flow]], colWidths=[17.8 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                           ("BOX", (0, 0), (-1, -1), 0.8, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t

def header(story, subtitle):
    story += [Paragraph("SynapSting", TIT), Spacer(1, 2), Paragraph(subtitle, SUB), Spacer(1, 3),
              Paragraph(f"<b>{C['aluno']}</b> · {C['serie']} · {C['escola']} · Orientador: {C['orientador']} · "
                        f"Projeto para a FEBRACE 2027", SM), Spacer(1, 4)]

def footer_line():
    return Paragraph(f"Contato: {C['email_aluno']} · {C['telefone']} · orientador: {C['email_orientador']} · "
                     f"Código aberto: {C['repo']}", SM)

# ------------------------------------------------------------------ 1 página
def one_pager(path="docs/resumo_1pagina.pdf"):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=1.6*cm, rightMargin=1.6*cm, topMargin=1.3*cm,
                            bottomMargin=1.1*cm, title="SynapSting — resumo", author=C["aluno"])
    s = []
    header(s, "Um gêmeo digital do cérebro da mosca-da-fruta para prever o efeito do inseticida imidacloprido "
              "no comportamento e testar essas previsões em moscas reais")
    s += [Paragraph("O problema", H), Paragraph(
        "O imidacloprido, um neonicotinoide, age nos receptores nicotínicos de acetilcolina dos insetos. Em doses que não "
        "matam, já prejudica a resposta de abelhas ao açúcar. O tema está em discussão no Ibama e na Justiça brasileira. "
        "Hoje, prever quais circuitos do cérebro são mais vulneráveis exige ensaios lentos, dose a dose.", B),
        Paragraph("A ideia", H), Paragraph(
        "Usar o modelo do cérebro inteiro da <i>Drosophila</i> (≈139 mil neurônios, conectoma FlyWire; Shiu et al., "
        "<i>Nature</i> 2024) como gêmeo digital. Simulamos dois mecanismos do inseticida, <b>bloqueio</b> das sinapses "
        "colinérgicas e <b>agonismo tônico</b>. Registramos as previsões publicamente e depois as testamos com o reflexo "
        "de extensão da probóscide (PER), medido por um instrumento de baixo custo que estou construindo (Arduino e câmera).", B),
        Paragraph("O que já temos", H)]
    s += bullets([
        "Simulador próprio validado contra o modelo original: correlação de <b>0,999</b> entre neurônios; "
        "neurônio motor do PER (MN9) a 94,7 Hz contra 93,3 Hz no original.",
        "Bloquear <b>10%</b> da transmissão colinérgica eleva o limiar do reflexo de 74,5 para 105 Hz (+41%); "
        "<b>30%</b> de bloqueio abole a resposta.",
        "Os dois mecanismos se separam com açúcar forte: o bloqueio reduz a resposta máxima, o agonismo tônico a "
        "preserva. É um teste simples para decidir entre eles em moscas reais.",
        "A limpeza das antenas parece mais vulnerável que a alimentação; no cérebro com fiação embaralhada, o circuito não responde.",
    ])
    s += [Spacer(1, 3), Image("figures/fig_resumo.png", width=17.8*cm, height=17.8*cm*2.5/7.2),
          Paragraph("Resultados preliminares (3 a 5 simulações por condição; serão refeitos com 30 antes do pré-registro). "
                    "Barras de erro: desvio-padrão entre simulações.", CAP)]
    ask = [Paragraph("<b>Como um laboratório pode ajudar</b> (qualquer um destes itens já ajuda muito)", B)] + bullets([
        "<b>Supervisão como cientista qualificado(a)</b> para o manuseio do imidacloprido, exigida pela FEBRACE "
        "para agrotóxicos (Formulário 2B).",
        "<b>Espaço de bancada</b> algumas horas por semana, entre novembro de 2026 e janeiro de 2027.",
        "<b>Moscas de uma linhagem selvagem</b> (Canton-S ou similar) e orientação de manejo e do ensaio de PER.",
        "Uma <b>conversa de 15 minutos</b> para críticas ao desenho experimental.",
    ]) + [Paragraph("Material de consumo e equipamento de filmagem por nossa conta [confirmar]. Preciso confirmar o apoio "
                    "até <b>07/10/2026</b> para incluir os formulários na inscrição.", B)]
    s += [Spacer(1, 5), box(ask), Spacer(1, 3)]
    CH = S("ch", 7.6, 9.4, "DVB", AZUL); CB = S("cb", 7.2, 9, "DV")
    crono = Table([[Paragraph(x, CH) for x in ["Até 16/10/2026", "Novembro/2026", "Nov/2026 a jan/2027", "Março/2027"]],
                   [Paragraph(x, CB) for x in ["Simulações finais, pré-registro público e inscrição",
                    "PER-bot validado e curva de moscas sem tratamento", "Experimento com imidacloprido, cego",
                    "Mostra FEBRACE"]]], colWidths=[4.45*cm]*4)
    crono.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "DVB", 7.6), ("FONT", (0, 1), (-1, 1), "DV", 7.2),
                               ("TEXTCOLOR", (0, 0), (-1, 0), AZUL), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LINEABOVE", (0, 0), (-1, 0), 0.6, AZUL), ("TOPPADDING", (0, 0), (-1, -1), 2),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    s += [crono, Spacer(1, 4), footer_line(),
          Paragraph("O código inicial foi escrito com assistência de IA; o aluno revisa, executa e estende todas as etapas.", SM)]
    doc.build(s)

# ------------------------------------------------------------------ 2 páginas (revisor)
def reviewer(path="docs/resumo_revisor_2paginas.pdf"):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=1.6*cm, rightMargin=1.6*cm, topMargin=1.3*cm,
                            bottomMargin=1.2*cm, title="SynapSting — resumo técnico", author=C["aluno"])
    s = []
    header(s, "Resumo técnico para revisão: perturbações colinérgicas no modelo LIF do cérebro inteiro de Drosophila")
    s += [Paragraph("1. Modelo e implementação", H), Paragraph(
        "Modelo LIF de Shiu et al. (2024) sobre o conectoma FlyWire v783 (138.639 neurônios; 15,1 milhões de pares). "
        "Parâmetros originais: v<sub>rep</sub> = −52 mV, v<sub>lim</sub> = −45 mV, τ<sub>m</sub> = 20 ms, τ<sub>s</sub> = 5 ms, "
        "refratário 2,2 ms, atraso 1,8 ms, w<sub>syn</sub> = 0,275 mV por sinapse. Neurotransmissor por neurônio: campo "
        "top_nt das anotações FlyWire (86.025 colinérgicos; 99,1% das suas arestas têm sinal excitatório no modelo).", B2),
        Paragraph(
        "Reimplementamos o modelo em NumPy, com assistência de IA, atualizando só os neurônios fora do repouso. "
        "Validação: (i) rede de teste com 2.000 neurônios contra o código original em Brian2, r = 0,9997; (ii) cérebro "
        "inteiro, açúcar a 200 Hz, contra os dados publicados de Shiu, r = 0,999 entre neurônios, MN9 94,7 vs 93,3 Hz. "
        "Detalhe encontrado na comparação: no Brian2, entradas que chegam durante o refratário são descartadas; sem essa "
        "regra, a atividade fica 22–38% acima da original.", B2),
        Paragraph("2. Perturbações", H)]
    s += bullets([
        "<b>Modo A (bloqueio/dessensibilização):</b> pesos de toda aresta com pré-sináptico colinérgico × (1 − α).",
        "<b>Modo B (agonista tônico):</b> despolarização constante b<sub>i</sub> = w<sub>syn</sub> · N<sub>i</sub><super>ACh</super> "
        "· ρ · τ<sub>s</sub>, o valor médio de cada sinapse colinérgica disparando a ρ Hz. Com ρ = 1 Hz, 229 neurônios "
        "passam a disparar espontaneamente.",
        "<b>Controles:</b> conectoma com alvos permutados (graus preservados) e triagem de gargalos (silenciar 1 neurônio "
        "colinérgico por vez).",
    ], BUL2)
    rows = [["Condição", "Alimentação 100 Hz", "Alimentação 200 Hz", "Água 200 Hz", "Limpeza 200 Hz"],
            ["Bloqueio α = 0,10", "58%", "83%", "—", "54%"],
            ["Bloqueio α = 0,15", "26%", "70%", "1%", "—"],
            ["Bloqueio α = 0,20", "3%", "49%", "—", "4%"],
            ["Agonista ρ = 0,5 Hz", "55%", "94%", "—", "—"],
            ["Agonista ρ = 1 Hz", "22%", "94%", "3%", "0%"]]
    t = Table(rows, colWidths=[4.2*cm, 3.4*cm, 3.4*cm, 3.2*cm, 3.6*cm])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "DVB", 7.8), ("FONT", (0, 1), (-1, -1), "DV", 7.8),
                           ("TEXTCOLOR", (0, 0), (-1, 0), AZUL), ("LINEBELOW", (0, 0), (-1, 0), 0.6, AZUL),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f4f7")]),
                           ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    s += [Paragraph("3. Resultados preliminares", H), Paragraph(
        "Limiar S50 (ajuste de Hill, IC 95% por bootstrap): 74,5 Hz [70,9–78,0] no controle; 105,1 [99,9–111,3] com α = 0,10; "
        "146,5 [135,2–166,2] com α = 0,20; sem resposta até 200 Hz com α ≥ 0,30. Resposta em % do controle (leitura: MN9 "
        "para alimentação e água; aDN1 para limpeza):", B2), Spacer(1, 2), t, Spacer(1, 2),
        Paragraph("3 a 5 tentativas de 1 s por condição (Modo B: 2 de 0,5 s). Conectoma embaralhado: MN9 = 0 Hz e 31–81 neurônios "
                  "recrutados, contra 234–298 no real. Maior queda ao silenciar um único neurônio colinérgico: 21% (CB0393).", CAP),
        Spacer(1, 3), Image("figures/fig_resumo.png", width=17.8*cm, height=17.8*cm*2.5/7.2),
        PageBreak(), Paragraph("4. O que me surpreendeu", H), Paragraph(
        "Esperava que o agonismo tônico facilitasse respostas (por exemplo, PER à água). O modelo prevê o contrário: "
        "a resposta à água cai para 3% e a limpeza é abolida, enquanto a alimentação com açúcar forte é preservada. "
        "Minha hipótese é recrutamento de interneurônios inibitórios (GABA e glutamato) que também recebem entrada "
        "colinérgica. Ainda não testei isso diretamente no modelo.", B2),
        Paragraph("5. Perguntas para o revisor", H)]
    s += [Paragraph(f"{i}. {q}", BUL2) for i, q in enumerate([
        "A formulação do Modo B como corrente constante proporcional ao número de sinapses colinérgicas de entrada é "
        "razoável, ou deveria ser uma condutância com dessensibilização dependente do tempo?",
        "Tratar todos os neurônios colinérgicos como igualmente sensíveis é aceitável como primeira aproximação, dado que "
        "a sensibilidade ao imidacloprido depende da composição de subunidades do nAChR?",
        "O controle com conectoma embaralhado destrói o caminho açúcar → MN9. Qual controle seria mais informativo: "
        "recrutamento em função de α, reatribuir quais neurônios são colinérgicos, ou outro?",
        "A comparação com moscas depende de mapear taxa de disparo dos GRNs para concentração de sacarose. Comparar só a "
        "forma das curvas, após calibração com moscas sem tratamento, é defensável?",
        "Há algum resultado da literatura de nAChR em Drosophila que contradiga diretamente essas previsões?",
    ], 1)]
    s += [Paragraph("6. Limitações declaradas", H)] + bullets([
        "O modelo não tem disparo basal, junções elétricas nem neuromodulação além de excitação e inibição.",
        "α e ρ não têm correspondência direta com concentração; o objetivo é prever direção e forma, não a dose exata.",
        "Mosca, e não abelha: sensibilidade diferente ao imidacloprido; a transferência para abelhas é um passo futuro.",
        "Poucas simulações por condição; a rodada final terá 30 tentativas e será pré-registrada antes das moscas.",
    ], BUL2) + [Paragraph("7. Como os dados reais vão testar o modelo", H), Paragraph(
        "Calibração com moscas sem tratamento (30 moscas, 7 concentrações de sacarose). Depois, veículo e três concentrações "
        "subletais de imidacloprido, com pelo menos 30 moscas por grupo, cegamento por códigos sorteados e análise pré-registrada: "
        "EC50 por grupo com bootstrap por mosca e modelo logístico com a mosca como agrupamento. Medidas: PER à sacarose, "
        "PER à água e limpeza das antenas.", B2),
        Spacer(1, 8), footer_line(),
        Paragraph("Código inicial escrito com assistência de IA (Claude); o aluno revisa, executa e estende. "
                  "Tabela de contribuição completa no relatório.", SM)]
    doc.build(s)

one_pager(); reviewer()
from pypdf import PdfReader
for p in ["docs/resumo_1pagina.pdf", "docs/resumo_revisor_2paginas.pdf"]:
    print(p, len(PdfReader(p).pages), "página(s)")
