# SynapSting

![testes](https://github.com/EnricoGaiottoM/SynapSting/actions/workflows/testes.yml/badge.svg)

**Começando do zero? Siga [docs/GUIA_INICIO.md](docs/GUIA_INICIO.md).**

Um gêmeo digital do cérebro de *Drosophila* para prever e testar o efeito subletal do imidacloprido
em circuitos sensório-motores. Projeto para a FEBRACE 2027.

## Instalação rápida
```bash
conda env create -f environment.yml && conda activate synapsting
python scripts/setup_data.py --all
python -m synapsting.check && python -m pytest
```

## Instalação manual (alternativa)
```bash
pip install -r requirements.txt
git clone https://github.com/philshiu/Drosophila_brain_model.git   # dados do conectoma (Shiu et al. 2024)
mkdir -p data && cp Drosophila_brain_model/{Completeness_783.csv,Connectivity_783.parquet} data/
cp Drosophila_brain_model/2023_03_23_completeness_630_final.csv data/Completeness_630.csv
cp Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet data/Connectivity_630.parquet
curl -L -o data/flywire_annotations_783.tsv \
  https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/Supplemental_file1_neuron_annotations.tsv
```
`data/neuron_ids_630.json` (já incluso) tem os IDs de neurônios extraídos de `figures.ipynb` de Shiu.

## Ordem de execução
| Passo | Comando | O que faz |
|---|---|---|
| 1 | `PYTHONPATH=. python scripts/01_validate.py <sugarR.parquet>` | Confere o simulador contra o Brian2 original |
| 2 | `PYTHONPATH=. python scripts/run_stage.py feeding A 0,0.05,0.1,0.15,0.2,0.3,0.4 --trials 30` | Grade do Modo A |
| 3 | `... run_stage.py feeding B 0.5,1,1.5,2 --trials 30` | Grade do Modo B (lento: atividade espontânea) |
| 4 | `... run_stage.py water|grooming|shuffle ...` | Água, limpeza, controle embaralhado |
| 5 | `PYTHONPATH=. python scripts/screen_bottlenecks.py --top 40 --trials 10` | Triagem de gargalos |
| 6 | `PYTHONPATH=. python scripts/analyze_preliminary.py` | Ajustes, bootstrap, figuras |

Dica: use vários terminais (um por nível) para usar todos os núcleos do computador.

## Estrutura
- `synapsting/` — conectoma, simulador LIF orientado a eventos, perturbações (Modos A/B), análise
- `scripts/` — validação, grades, gargalos, figuras
- `results/`, `figures/` — resultados preliminares (26/09/2026, poucas tentativas: refazer com ≥ 30)
- `perbot/` — firmware Arduino, pontuação por vídeo (OpenCV) e kappa
- `fly_stats/` — cegamento e análise pré-registrada dos dados de moscas
- `prereg/PREREGISTRO.md` — registro de previsões (publicar antes das moscas)

## Validação (26/09/2026)
- Rede de teste (2.000 neurônios) contra o código original em Brian2: r = 0,9997; atividade total 1,001×.
- Cérebro inteiro (v630, açúcar 200 Hz) contra `results/example/sugarR.parquet`: r = 0,999; MN9 94,7 vs 93,3 Hz.
- Detalhe crítico: no Brian2, entradas que chegam durante o refratário são descartadas.
  Sem isso, a atividade fica 22–38% acima da original.

## Créditos
Modelo e dados: Shiu et al. (2024), Dorkenwald et al. (2024), Schlegel et al. (2024), Eckstein et al. (2024), consórcio FlyWire.
Código do modelo original: licença MIT. Anotações FlyWire: ver licença do repositório flyconnectome/flywire_annotations.

## Anexos para contato com laboratórios
Edite `docs/contato.json` (nome, escola, orientador, e-mails, link do GitHub) e rode:
```bash
python docs/make_figure_resumo.py && python docs/make_summaries.py
```
Gera `docs/resumo_1pagina.pdf` (pedido de apoio) e `docs/resumo_revisor_2paginas.pdf` (revisão do modelo).

## Como este código foi feito
A versão inicial do simulador, das análises e das ferramentas foi escrita com assistência de IA (Claude). O aluno revisa, executa, valida e estende o código; a tabela de contribuição do relatório detalha cada parte.
