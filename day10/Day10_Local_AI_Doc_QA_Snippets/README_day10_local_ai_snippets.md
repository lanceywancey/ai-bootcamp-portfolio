# Day 10 Local AI Snippets

## One-time setup while online
```bash
pip install -r requirements_day11_local_ai.txt
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

## Offline use
After dependencies and models are installed, disconnect from the internet and run:
```bash
python practice_01_check_ollama.py
python practice_02_load_many_files.py
python practice_03_chunk_embed_store.py
python practice_04_retrieve_test.py
python practice_05_local_doc_qa_cli.py
streamlit run practice_06_final_streamlit_local_doc_chatbot.py
```

Put test files inside the `docs/` folder for practices 2-5.
