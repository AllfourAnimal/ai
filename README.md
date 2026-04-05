ai server

## Recommendation Demo

The recommendation server reads demo data directly from `data/seoul_animals.db`.

```bash
conda create -n ai-server python=3.9 -y
conda activate ai-server
pip install -r requirements.txt
PYTHONPATH=src python -m uvicorn recommendation_server.app.main:app --host 127.0.0.1 --port 8001 --reload
```
