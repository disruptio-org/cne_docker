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

## Resolução de problemas comuns

### Erro `open //./pipe/dockerDesktopLinuxEngine`

Ao executar `docker compose -f docker-compose.min.yml up --build -d` no Windows, você pode ver a mensagem:

```
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

Esse erro indica que o Docker Engine não está acessível pelo Docker Desktop. Para corrigir:

1. **Verifique se o Docker Desktop está aberto**
   - Inicie o Docker Desktop manualmente. Aguarde até que o ícone na bandeja de sistema indique "Docker Desktop is running".

2. **Confirme o funcionamento do WSL 2** (necessário para o Docker Desktop no Windows)
   - Execute no PowerShell (como usuário comum) `wsl --status`. Caso o WSL 2 não esteja instalado ou atualizado, siga as instruções exibidas para concluir a instalação.
   - Reinicie o computador se solicitado.

3. **Teste a conexão com o Docker Engine**
   - Rode `docker version` ou `docker info`. Se os comandos retornarem informações do servidor, tente novamente o `docker compose -f docker-compose.min.yml up --build -d`.

4. **Reinicie os serviços do Docker Desktop**
   - Se o erro persistir, utilize a opção **Troubleshoot → Restart Docker Desktop** no aplicativo ou finalize o processo `Docker Desktop.exe` e abra-o novamente.

Após essas etapas, o Docker Compose deve conseguir baixar a imagem `cne/api:fixed-v2` e iniciar os contêineres normalmente.
