# config/settings.py
#
# --- Carregamento do token do X (Twitter) DESATIVADO por enquanto ---
# Este módulo existe só para o scraping do X (Bearer Token). Foi comentado
# junto com o restante da integração do X. Para reativar, descomente abaixo
# e os arquivos src/utils/X/*.py e o bloco x_search em scraper.py.
#
# from __future__ import annotations
#
# import os
# from datetime import datetime, timezone
# from typing import Any, Dict, List
# from pathlib import Path
#
# from dotenv import load_dotenv
#
# BASE_DIR = Path(__file__).resolve().parent.parent
# load_dotenv(BASE_DIR / "keys.env")
#
# X_BEARER_TOKEN = Path(os.getenv("X_BEARER_TOKEN"))
#
# if not X_BEARER_TOKEN:
#     raise RuntimeError("Bearer token not defined at .env")
