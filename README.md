## Artefato FOPM — Projeção de DRE

Este repositório contém o motor de projeção da DRE da BU **FOPM Brasil** (2026–2030), além dos dados históricos e saídas em CSV.

### Estrutura de pastas

- `projecao_bus/` — código-fonte do motor de projeção (`fopm.py`) e CSVs de projeção gerados.
  - `fopm.py` — implementa a projeção linha a linha conforme o documento de plano.
  - `projecoes/` — arquivos de saída gerados pelo código (ex.: `projecao_fopm_brasil.csv`).
- `data/` — arquivos CSV de **dados históricos** e **derivações** não geradas automaticamente pelo código.
  - `dre_fopm_historico.csv` — histórico DRE 2018–2025 usado como base para cálculo dos drivers.
  - `dre_fopm_projecao.csv` — DRE projetada em formato pivotado (linhas = contas, colunas = anos), derivada da projeção.
- `docs/` — documentação e especificações funcionais.
  - `planfopm.md` — plano detalhado de implementação do motor de projeção.

### Fluxo principal

1. Ler o histórico DRE 2018–2025 de `data/dre_fopm_historico.csv`.
2. Calcular os drivers médios (ratios e bases) com base em 2023–2025.
3. Projetar a DRE da FOPM Brasil de 2026 a 2030 com as premissas de inflação, headcount e ociosidade.
4. Salvar a projeção granular em `projecao_bus/projecoes/projecao_fopm_brasil.csv`.
5. (Opcional) Derivar e atualizar a visão em formato de DRE (`data/dre_fopm_projecao.csv`) a partir da projeção granular.

### Como rodar a projeção

Requisitos:

- Python 3.10+ (recomendado)
- Dependências: `pandas`, `numpy`

Exemplo rápido de uso:

```bash
cd artefato_calculadora
python -m projecao_bus.fopm
```

Após a execução, o arquivo `projecao_bus/projecoes/projecao_fopm_brasil.csv` será atualizado com a projeção mais recente.

