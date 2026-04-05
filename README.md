ai server

## Sync Animal DB

1. Create a conda environment with Python 3.9.
2. Install dependencies from `requirements.txt`.
3. Create a repository root `.env` file based on `.env.example`.
4. Set `ANIMAL_API_SERVICE_KEY`.
5. Run `PYTHONPATH=src python -m database` or `animal-sync`.

This syncs all Seoul districts into a local SQLite database. The recommendation server reads only from that database.
