ai server

## Animal Abandonment Ingestion

1. Create a conda environment with Python 3.9.
2. Install dependencies from `requirements.txt`.
3. Create a repository root `.env` file based on `.env.example`.
4. Set `ANIMAL_API_SERVICE_KEY`.
5. Run `PYTHONPATH=src python -m database --district 동대문구 --district 강남구 --limit 100`.

The demo saves a simplified JSON response to the repository `output/` directory by default, including shelter metadata and up to the requested number of animals.
