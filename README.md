# cne_docker

## Ciclo de ensino do motor

Para ensinar o motor de NER, siga sempre o mesmo ciclo. Cada iteração garante que os dados estão padronizados e que o treinamento pode ser reproduzido.

1. **Preparar o pack de treino**
   - Crie uma pasta `pack_XXX/` (substitua `XXX` pelo identificador da rodada) contendo:
     - `pack_XXX/input.docx`: o documento linearizado que servirá como base do corpus.
     - `pack_XXX/gold.csv`: a planilha com as anotações de entidades, com colunas `text`, `label`, `start`, `end`.
   - Gere o `gold.csv` diretamente a partir do Excel/LibreOffice. Salve em **UTF-8 com BOM (`utf-8-sig`)** quando o arquivo contiver caracteres especiais (acentos, emoji, etc.). Use **CP-1252** apenas quando o consumidor final exigir compatibilidade com versões antigas do Excel no Windows e o conteúdo estiver limitado a caracteres latinos básicos.

2. **Linearizar o documento**
   - Execute `doc_linearize pack_XXX/input.docx > pack_XXX/input.txt` para transformar o `.docx` em texto plano preservando a ordem do documento.

3. **Montar o corpus**
   - Rode `make_corpus --input pack_XXX/input.txt --gold pack_XXX/gold.csv --output data/corpus_XXX.jsonl`.

4. **Treinar o modelo**
   - Use `train --corpus data/corpus_XXX.jsonl --model models/model_XXX`. Caso precise habilitar perguntas e respostas durante o treinamento, adicione o parâmetro `qa=true` no arquivo de configuração (por exemplo, em `config/train.yml`).

5. **Ativar regras rígidas de template**
   - Para ambientes que exigem validação estrita de templates, defina `STRICT_TEMPLATES=true` na configuração ou variável de ambiente antes de iniciar o `train`.

6. **Executar o NER**
   - Com o modelo treinado, execute `use_ner --model models/model_XXX --input data/corpus_XXX.jsonl --output outputs/predictions_XXX.csv`.

Seguir estes passos garante que o motor seja ensinado de forma consistente, facilitando auditoria e reprodução dos resultados.

## Run

### Build & Run

```bash
docker compose -f docker-compose.min.yml up --build -d
curl http://localhost:8010/health

Extract
curl -F "file=@data/1503_Almada_441 Listas admitidas ASSEMBLEIA E CAMARA.docx" \
     -F "operator=A" -F "ord_reset=true" -F "enable_ia=false" \
     http://localhost:8010/extract
```
