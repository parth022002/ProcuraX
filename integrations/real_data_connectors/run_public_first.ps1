# Run the no-key source first, followed by optional authenticated sources.
# Execute from the project folder after setup: .\run_public_first.ps1
python src/fetch_gdelt.py
python src/fetch_marketaux.py
python src/fetch_alpha_vantage.py
python src/fetch_newsdata.py
python src/fetch_sec_edgar.py
