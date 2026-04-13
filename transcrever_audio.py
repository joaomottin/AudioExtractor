from __future__ import annotations

from datetime import datetime
from pathlib import Path
import traceback

import ffmpeg
import whisper
from tqdm import tqdm

try:
    import torch
except ImportError:  # fallback caso torch nao esteja acessivel diretamente
    torch = None


ROOT_DIR = Path(__file__).resolve().parent
AUDIOS_DIR = ROOT_DIR / "Audios"
TRANSCRICOES_DIR = ROOT_DIR / "Transcricoes"
LOG_ERROS = ROOT_DIR / "log_erros.txt"
MODEL_NAME = "medium"  # use "large" se quiser mais precisao e tiver recursos


def registrar_erro(arquivo: Path, erro: Exception) -> None:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with LOG_ERROS.open("a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] Falha ao processar: {arquivo.name}\n")
        log.write(f"Erro: {erro}\n")
        log.write(traceback.format_exc())
        log.write("\n" + ("-" * 80) + "\n")


def garantir_pastas() -> None:
    if not AUDIOS_DIR.exists():
        raise FileNotFoundError(
            f"Pasta de audios nao encontrada em: {AUDIOS_DIR}"
        )
    TRANSCRICOES_DIR.mkdir(parents=True, exist_ok=True)


def listar_mp4s() -> list[Path]:
    return sorted(AUDIOS_DIR.glob("*.mp4"))


def obter_duracao_segundos(caminho_arquivo: Path) -> float:
    probe = ffmpeg.probe(str(caminho_arquivo))
    format_info = probe.get("format", {})
    return float(format_info.get("duration", 0.0) or 0.0)


def extrair_wav_temporario(video_path: Path, wav_path: Path) -> None:
    (
        ffmpeg
        .input(str(video_path))
        .output(
            str(wav_path),
            acodec="pcm_s16le",
            ar=16000,
            ac=1,
            vn=None,
            loglevel="error",
        )
        .overwrite_output()
        .run(quiet=True)
    )


def formatar_duracao_minutos(segundos: float) -> str:
    minutos = max(1, round(segundos / 60)) if segundos > 0 else 0
    return f"{minutos} min"


def montar_markdown(
    nome_base: str,
    nome_origem: str,
    duracao_segundos: float,
    texto_transcricao: str,
) -> str:
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
    duracao_estimada = formatar_duracao_minutos(duracao_segundos)

    return (
        f"# Transcrição: {nome_base}\n\n"
        f"**Data de geração:** {data_geracao}  \n"
        f"**Arquivo de origem:** {nome_origem}  \n"
        f"**Duração estimada:** {duracao_estimada}\n\n"
        "---\n\n"
        f"{texto_transcricao.strip()}\n"
    )


def transcrever_arquivo(modelo: whisper.Whisper, mp4_path: Path, indice: int, total: int) -> None:
    nome_base = mp4_path.stem
    md_path = TRANSCRICOES_DIR / f"{nome_base}.md"

    if md_path.exists():
        print(f"[{indice}/{total}] Pulando '{mp4_path.name}' (ja transcrito).")
        return

    wav_path = AUDIOS_DIR / f"{nome_base}__temp.wav"

    try:
        print(f"[{indice}/{total}] Processando: {mp4_path.name}")

        duracao_segundos = obter_duracao_segundos(mp4_path)
        print("  - Extraindo audio para WAV temporario...")
        extrair_wav_temporario(mp4_path, wav_path)

        usar_fp16 = bool(torch and torch.cuda.is_available())
        print(
            "  - Iniciando transcricao (modelo "
            f"{MODEL_NAME}, language='pt', fp16={usar_fp16})..."
        )

        resultado = modelo.transcribe(
            str(wav_path),
            language="pt",
            fp16=usar_fp16,
            verbose=False,
        )

        segmentos = resultado.get("segments", []) or []
        if segmentos and duracao_segundos > 0:
            print("  - Progresso por segmento:")
            for seg in tqdm(segmentos, desc="    Segmentos", unit="seg"):
                fim = float(seg.get("end", 0.0) or 0.0)
                percentual = min(100.0, (fim / duracao_segundos) * 100)
                print(
                    f"    [{percentual:6.2f}%] "
                    f"{seg.get('start', 0.0):.1f}s -> {seg.get('end', 0.0):.1f}s"
                )

        markdown = montar_markdown(
            nome_base=nome_base,
            nome_origem=mp4_path.name,
            duracao_segundos=duracao_segundos,
            texto_transcricao=resultado.get("text", ""),
        )

        md_path.write_text(markdown, encoding="utf-8")
        print(f"  - Transcricao salva em: {md_path}")

    except Exception as erro:
        print(f"  - ERRO em '{mp4_path.name}': {erro}")
        registrar_erro(mp4_path, erro)
    finally:
        if wav_path.exists():
            wav_path.unlink(missing_ok=True)
            print("  - WAV temporario removido.")


def main() -> None:
    try:
        garantir_pastas()
    except FileNotFoundError as erro:
        print(f"Erro: {erro}")
        return

    arquivos_mp4 = listar_mp4s()
    if not arquivos_mp4:
        print("Nenhum arquivo .mp4 encontrado em Audios/.")
        return

    print(f"Carregando modelo Whisper '{MODEL_NAME}'...")
    modelo = whisper.load_model(MODEL_NAME)

    total = len(arquivos_mp4)
    print(f"{total} arquivo(s) encontrado(s) para avaliacao.\n")

    for indice, mp4_path in enumerate(arquivos_mp4, start=1):
        transcrever_arquivo(modelo, mp4_path, indice, total)
        print()

    print("Processamento concluido.")


if __name__ == "__main__":
    main()
