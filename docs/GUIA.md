# Guia: do zero ao primeiro resultado

Tudo roda no **GitHub Codespaces**, no navegador. Nada precisa ser instalado no computador.

## 1. Abrir o ambiente

1. No repositório, clique em **Code** → **Codespaces** → abra o Codespace existente (ou crie um em `main`).
2. No terminal, uma vez por Codespace:

```bash
pip install -e ".[dev,docs]"
python scripts/baixar_dados.py --all
```

## 2. Conferir que tudo funciona

```bash
python -m synapsting.check
python -m pytest
python scripts/validar.py
```

Esperado: "OK: instalação funcionando", "9 passed", e correlação acima de 0,99 com o MN9 perto de 93 Hz.
Anote os três resultados no diário.

## 3. Rotina de cada dia

```bash
git pull
# ... trabalho ...
git add -A
git commit -m "Verbo no presente: o que mudou"
git push
```

Um registro por dia em `docs/diario/`, copiando `MODELO.md`. Para fechar uma tarefa no commit: `(closes #3)`.

## 4. Grade final (até 04/10)

1. Troque a máquina do Codespace para **4-core** (Code → Codespaces → ⋯ → Change machine type).
2. Em Settings → Codespaces, ponha o **Default idle timeout** em 240 minutos.
3. Rode e, depois, analise:

```bash
python scripts/rodar_grade.py configs/teste.json
python scripts/rodar_grade.py configs/final.json --jobs 4
python scripts/gargalos.py --top 40 --trials 10
python scripts/analisar.py resultados/final
```

Se o Codespace desligar, rode o mesmo comando: ele continua de onde parou.
Não altere `configs/final.json` depois do pré-registro.

## 5. Pré-registro (até 09/10)

1. Preencha `docs/PREREGISTRO.md` com os números de `resultados/final/`.
2. Congele:

```bash
git add -A && git commit -m "Pré-registro das previsões"
git tag -a prereg-v1 -m "Previsões antes dos experimentos com moscas"
git push && git push --tags
```

3. Crie uma **Release** da tag `prereg-v1` no GitHub e registre também no OSF (osf.io → Registries).

## 6. Resumos em PDF para os e-mails

Preencha `configs/contato.json` e rode:

```bash
sudo apt-get install -y fonts-dejavu-core fonts-dejavu-extra
python scripts/resumos.py
```

## 7. No fim do dia

Pare o Codespace (github.com/codespaces → ⋯ → Stop) para não gastar a cota mensal.

## Problemas comuns

| Sintoma | Solução |
| --- | --- |
| `MemoryError` ou travamento | Diminua `--jobs` |
| MN9 = 0 no check | `python scripts/baixar_dados.py --verify` |
| `rejected ... fetch first` no push | `git pull --rebase` e depois `git push` |
| Teste falhou depois de mudar o simulador | O teste pegou um erro: desfaça e investigue |
