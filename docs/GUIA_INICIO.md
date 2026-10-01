# Guia de início: do zero ao primeiro resultado

Siga na ordem. Cada passo tem um "pronto quando" para você saber que deu certo.
Tempo total: cerca de 2 horas, a maior parte esperando downloads e instalações.

## 1. Instalar as ferramentas (uma vez)

| Ferramenta | Para quê | Onde |
| --- | --- | --- |
| Git | Controle de versão | git-scm.com (no Windows, instale junto o **Git Bash**) |
| Miniconda | Python 3.11 isolado do sistema | docs.conda.io/en/latest/miniconda.html |
| VS Code | Editor | code.visualstudio.com (extensão "Python") |
| GitHub CLI | Criar tarefas e marcos por script | cli.github.com |

Pronto quando: `git --version`, `conda --version` e `gh --version` respondem no terminal.

## 2. Criar a conta e o repositório no GitHub

1. Crie a conta em github.com com o e-mail do aluno.
2. Em **Settings → Emails**, marque **"Keep my email addresses private"** e anote o endereço
   `...@users.noreply.github.com`. Ele vai nos commits no lugar do e-mail real.
3. Clique em **New repository**: nome `SynapSting`, **Public**, **sem** README, licença ou .gitignore
   (o projeto já tem os três).

## 3. Preencher os dados pessoais

Troque os campos entre colchetes em: `LICENSE`, `CITATION.cff`, `docs/contato.json` e no link do GitHub
em `README.md`.

## 4. Primeiro envio

No terminal (Git Bash no Windows), dentro da pasta do projeto:

```bash
git config --global user.name "Nome do Aluno"
git config --global user.email "ID+usuario@users.noreply.github.com"
git init
git add .
git commit -m "Simulador validado, resultados preliminares e ferramentas do projeto"
git branch -M main
git remote add origin https://github.com/EnricoGaiottoM/SynapSting.git
gh auth login          # escolha GitHub.com, HTTPS, login pelo navegador
git push -u origin main
```

Pronto quando: os arquivos aparecem no GitHub e a aba **Actions** mostra os testes passando (bolinha verde).

## 5. Ambiente Python

```bash
conda env create -f environment.yml
conda activate synapsting
```

Sem conda: `python -m venv .venv`, ative o ambiente e rode `pip install -e ".[dev]"`.
Para o PER-bot e a validação com Brian2, depois: `pip install -e ".[perbot,validacao,docs]"`.

## 6. Dados do conectoma (~225 MB)

```bash
python scripts/setup_data.py --all
```

Os links apontam para versões fixas e cada arquivo é conferido por SHA-256.
Pronto quando: aparece "Tudo certo." Se algum der ERRO, apague o arquivo e rode de novo.

## 7. Conferir que tudo funciona (Decisão 1)

```bash
python -m synapsting.check
python -m pytest
python scripts/01_validate.py data/shiu_sugarR_200Hz.parquet
```

Pronto quando: o check diz "OK", os testes passam e a validação dá r > 0,99, com MN9 perto de 93 Hz.
**Anote os três resultados no Diário de Bordo, com data.** É a evidência da Decisão 1.

## 8. Tarefas e marcos no GitHub

```bash
bash scripts/github_bootstrap.sh
```

Cria etiquetas, 6 marcos com datas e as tarefas do cronograma. A partir daí, cada tarefa concluída é
fechada na aba **Issues**, e os avaliadores podem ver a história do projeto.

## 9. Rodar a grade final

Teste rápido primeiro:

```bash
python scripts/run_grid.py configs/grid_teste.json
```

Depois, a grade do pré-registro:

```bash
python scripts/run_grid.py configs/grid_final.json --jobs 4
```

- **--jobs**: use no máximo (RAM em GB) ÷ 2. Com 8 GB, use 3 ou 4.
- A estimativa aparece na tela. O Modo B é bem mais lento; deixe rodando à noite.
- Se o computador desligar, rode o mesmo comando: ele continua de onde parou.
- Resultados em `results/final/`. **Não altere `grid_final.json` depois do pré-registro.**

Computador fraco? Use o Google Colab: abra `notebooks/00_colab.ipynb`.

## 10. Rotina diária

```bash
git pull                                   # se mais alguém mexeu
# ... trabalho ...
git add -A
git commit -m "Adiciona análise de recrutamento no Modo B"   # verbo no presente, uma ideia por commit
git push
```

- Um registro por dia em `docs/diario/` (copie `MODELO.md`), além do Diário de Bordo oficial.
  Confira nas regras da FEBRACE o formato exigido.
- **Nunca** envie para o GitHub: dados do conectoma, vídeos brutos, `chave_SECRETA.csv`. O `.gitignore`
  já bloqueia esses arquivos.

## 11. Publicar o pré-registro (antes de qualquer mosca receber inseticida)

1. Preencha `prereg/PREREGISTRO.md` com os números da grade final e o n da simulação de poder.
2. Congele no Git:
   ```bash
   git add prereg/ configs/grid_final.json results/final/
   git commit -m "Pré-registro das previsões"
   git tag -a prereg-v1 -m "Pré-registro: previsões antes dos experimentos com moscas"
   git push && git push --tags
   ```
3. No GitHub, crie uma **Release** a partir da tag `prereg-v1`.
4. Registre também no **OSF** (osf.io → Registries): o carimbo de data fica num serviço independente,
   o que é mais forte que um commit.

## Problemas comuns

| Sintoma | Solução |
| --- | --- |
| `MemoryError` ou computador travando | Diminua `--jobs` |
| Download lento ou interrompido | Rode `setup_data.py` de novo |
| `bash` não existe no Windows | Use o Git Bash |
| MN9 = 0 no check | Rode `setup_data.py --verify`; algum arquivo pode estar corrompido |
| Testes falham depois de mudar o simulador | Bom sinal: o teste pegou o erro. Desfaça e investigue |
