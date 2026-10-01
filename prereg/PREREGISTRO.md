# Registro de previsões — SynapSting

**Data do registro:** ____/10/2026 (commit no GitHub = carimbo de data)  
**Autor:** ______ · **Orientador:** ______

> Regra: este arquivo é publicado ANTES de qualquer mosca receber imidacloprido.
> Depois de publicado, não se edita; correções vão num adendo datado.

## 1. Previsões do modelo (preencher com os números da rodada final)

| # | Previsão | Número do modelo | Critério de confirmação nas moscas |
|---|---|---|---|
| H1 | Imidacloprido aumenta o EC50 de sacarose do PER | S50 sobe de 74,5 Hz (α=0) para 105 Hz (α=0,10) e 147 Hz (α=0,20) | EC50 do grupo "média" > EC50 do veículo, IC 95% da razão acima de 1 |
| H3 | A limpeza das antenas é mais vulnerável que a alimentação | α=0,10 reduz limpeza para 54% e alimentação para 83% (estímulo máximo) | Queda relativa da limpeza > queda relativa do PER na mesma dose |
| H4 | Modo A reduz a resposta máxima; Modo B quase não reduz | Sacarose máxima: A (α=0,2) = 49% do controle; B (ρ=1) = 94% | PER à sacarose mais alta: cai (→A) ou se mantém (→B) |
| H4b | Nenhum modo aumenta a resposta à água | Água: A = 1%, B = 3% do controle | Resposta à água no tratado ≤ veículo |
| H5 | Moscas sem tratamento têm curva sigmoide como a do modelo | Hill n ≈ 4 | Ajuste logístico com inclinação > 0 e IC que não inclui 0 |

## 2. Desenho experimental
- Grupos: veículo + 3 concentrações (definidas no piloto de sobrevivência, mortalidade < 10% em 24 h).
- n: ≥ 30 moscas por grupo (justificar com a simulação de poder em `fly_stats/analyze_per.py`).
- Sacarose: 7 concentrações em série crescente, água entre elas; controle positivo no fim.
- Exclusões (definidas agora): mosca que não responde à sacarose mais alta; mosca morta ou solta.
- Cegamento: `fly_stats/randomize_blind.py`; a chave fica com o orientador.

## 3. Análise (definida agora)
- Primária: EC50 por grupo com IC 95% por bootstrap de moscas; razão EC50 tratado/veículo.
- Secundária: GEE binomial (ou GLMM `glmer`) com mosca como agrupamento.
- Medida de PER: PER-bot se kappa ≥ 0,8 na validação; senão, pontuação manual cega.

## 4. O que muda a conclusão
- Resultados contrários às previsões serão publicados como refutação, com a análise de onde o modelo falha.
