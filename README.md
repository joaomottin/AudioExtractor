# AudioExtractor

Projeto simples para transcrever audios de videos `.mp4` para texto em Markdown usando Whisper local.

## O que este projeto faz

- Busca arquivos `.mp4` na pasta `Audios/`
- Extrai audio para um arquivo WAV temporario
- Transcreve em portugues (`language='pt'`) com o modelo Whisper
- Gera um `.md` na pasta `Transcricoes/` com metadados e texto
- Pula arquivos que ja foram transcritos
- Registra falhas em `log_erros.txt`

## Estrutura esperada

```text
AudioExtractor/
|- transcrever_audio.py
|- Audios/
|- Transcricoes/
|- log_erros.txt (gerado quando houver erro)
```

## Requisitos

- Python 3.10+
- FFmpeg instalado e disponivel no `PATH`
- Dependencias Python:
  - `openai-whisper`
  - `ffmpeg-python`
  - `tqdm`
  - `torch` (opcional para acelerar com GPU)

## Instalacao

No Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install openai-whisper ffmpeg-python tqdm torch
```

Se voce quiser usar aceleracao por GPU NVIDIA, instale o `torch` conforme a recomendacao oficial do PyTorch para sua versao de CUDA.

## Como usar

1. Coloque os arquivos `.mp4` em `Audios/`.
2. Execute o script:

```powershell
python transcrever_audio.py
```

3. Confira os resultados em `Transcricoes/`.

## Ajustes rapidos

No arquivo `transcrever_audio.py`, voce pode trocar o tamanho do modelo:

- `MODEL_NAME = "medium"` (padrao atual)
- Outras opcoes comuns: `small`, `large`

Modelos maiores tendem a ser mais precisos, mas consomem mais tempo e recursos.

## Saida gerada

Cada transcricao e salva como:

- `Transcricoes/NomeDoArquivo.md`

Com o seguinte formato:

- Titulo da transcricao
- Data de geracao
- Nome do arquivo de origem
- Duracao estimada
- Texto transcrito

## Solucao de problemas

- Erro de `ffmpeg`: confirme se o FFmpeg esta instalado e acessivel no terminal (`ffmpeg -version`).
- Erros de dependencia: rode `pip install -U openai-whisper ffmpeg-python tqdm torch`.
- Lentidao: use um modelo menor (`small`) ou GPU, se disponivel.

## Observacoes

Este repositorio foi pensado para uso local e simples automacao de transcricoes em lote.
