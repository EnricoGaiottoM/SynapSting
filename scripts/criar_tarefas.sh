#!/usr/bin/env bash
# Cria etiquetas, marcos (com datas) e as tarefas do projeto no GitHub.
# Requer o GitHub CLI autenticado: gh auth login
# Uso (dentro da pasta do repositório, depois do primeiro push): bash scripts/criar_tarefas.sh
set -euo pipefail
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Configurando $REPO"

for l in "simulacao:1d76db" "laboratorio:d93f0b" "perbot:0e8a16" "relatorio:5319e7" "febrace:b60205" "tarefa:c5def5"; do
  gh label create "${l%%:*}" --color "${l##*:}" --force >/dev/null
done

marco() { gh api "repos/$REPO/milestones" -f title="$1" -f due_on="$2T23:59:59Z" -f description="$3" >/dev/null && echo "marco: $1"; }
marco "Decisão 1 - modelo roda"        2026-09-30 "Modelo instalado e validado no computador do aluno"
marco "Decisão 2 - laboratório"         2026-10-07 "Laboratório e cientista qualificado confirmados"
marco "Núcleo computacional"            2026-10-09 "Grades finais, gargalos e pré-registro publicado"
marco "Submissão FEBRACE"               2026-10-16 "Relatório, resumo, formulários e envio"
marco "PER-bot v1 e calibração"         2026-11-15 "Instrumento validado (kappa) e curva de moscas sem tratamento"
marco "Experimentos com imidacloprido"  2027-01-31 "Piloto, experimento principal cego e limpeza"

t() { gh issue create --title "$1" --label "$2" --milestone "$3" --body "$4" >/dev/null && echo "tarefa: $1"; }
t "Instalar ambiente e baixar dados (baixar_dados.py)" simulacao "Decisão 1 - modelo roda" "Pronto quando: baixar_dados.py --verify mostra tudo OK e python -m synapsting.check passa."
t "Validar simulador contra Brian2 (validar.py)" simulacao "Decisão 1 - modelo roda" "Pronto quando: r > 0,99 e MN9 a ±5 Hz do original. Registrar números no Diário."
t "Rodar testes automáticos (pytest)" simulacao "Decisão 1 - modelo roda" "Pronto quando: todos os testes passam localmente e no GitHub Actions."
t "Enviar e-mails aos laboratórios (rodada 1)" laboratorio "Decisão 2 - laboratório" "Prioridade 1 + Drosophila. Anotar data de envio de cada um."
t "Ligar para quem não respondeu" laboratorio "Decisão 2 - laboratório" "Quinta 01/10. Usar o roteiro."
t "Enviar e-mails (rodada 2) e plano B" laboratorio "Decisão 2 - laboratório" "Sexta 02/10."
t "Grade final Modo A e Modo B (30 tentativas)" simulacao "Núcleo computacional" "python scripts/rodar_grade.py configs/final.json --jobs N"
t "H2: recrutamento em função de alfa (real x embaralhado)" simulacao "Núcleo computacional" "Definir a métrica antes de olhar os dados finais."
t "Testar hipótese de recrutamento inibitório no Modo B" simulacao "Núcleo computacional" "Medir taxa média de neurônios GABA/Glu com e sem rho."
t "Triagem de gargalos (40 neurônios x 10 tentativas)" simulacao "Núcleo computacional" "scripts/gargalos.py --top 40 --trials 10"
t "Simulação de poder estatístico (n de moscas)" relatorio "Núcleo computacional" "Usar laboratorio/estatistica/analisar_moscas.py --demo como base. Fixar n no pré-registro."
t "Publicar pré-registro (tag + OSF)" relatorio "Núcleo computacional" "git tag prereg-v1 e registro no OSF antes de qualquer mosca receber inseticida."
t "Escrever relatório (métodos e resultados preliminares)" relatorio "Submissão FEBRACE" "Seguir estrutura FEBRACE; uma figura por hipótese."
t "Formulários e assinaturas" febrace "Submissão FEBRACE" "2A sempre; 2B, 2C e 3 se houver laboratório."
t "SUBMETER" febrace "Submissão FEBRACE" "Meta 16/10; limite 20/10 18h. Depois de submeter, nada muda."
t "Comprar peças do PER-bot" perbot "PER-bot v1 e calibração" "Arduino, servo SG90, microscópio USB, anel de LED, suporte 3D."
t "Montar PER-bot e calibrar a pontuação por vídeo" perbot "PER-bot v1 e calibração" "laboratorio/perbot/pontuar_video.py; escolher limiar z na calibração."
t "Validar PER-bot: kappa com avaliador cego (200 eventos)" perbot "PER-bot v1 e calibração" "Meta kappa >= 0,8 (laboratorio/perbot/kappa.py)."
t "Curva de PER em moscas sem tratamento (H5)" laboratorio "PER-bot v1 e calibração" "30 moscas, 7 concentrações."
t "Piloto de sobrevivência com imidacloprido" laboratorio "Experimentos com imidacloprido" "Só com cientista qualificado e formulários aprovados."
t "Experimento principal cego" laboratorio "Experimentos com imidacloprido" "laboratorio/estatistica/cegamento.py; chave com o orientador."
t "Acelerar o Modo B (regime denso)" simulacao "Núcleo computacional" "O Modo B mantém milhares de neurônios ativos e fica ~20x mais lento. Ideia: quando o conjunto ativo passar de ~20% da rede, trocar para atualização densa (vetores inteiros) ou PyTorch. Medir o ganho e validar com os testes."
echo "Pronto: veja as abas Issues e Milestones do repositório."
