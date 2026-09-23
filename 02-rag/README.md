# 02 — LangChain RAG: progressive local lab

Each committed stage below is independently runnable from this directory.
Install the pinned packages in `requirements.txt` into a Python virtual environment.
Use the locally loaded Foundry `qwen3-4b` model; no cloud key is required.

## Available concepts

1. **Local LLM baseline and FAQ**
   - `python src/stage_a_baseline.py`
2. **Document loader**
   - `python src/stage_b_loader.py`
3. **Text splitter**
   - `python src/stage_c_splitter.py`
4. **Local embedding**
   - `python src/stage_d_embedding.py`
5. **Vector store and similarity search**
   - `python src/stage_e_vectorstore.py`
6. **Retriever abstraction**
   - `python src/stage_f_retriever.py`

Run the stage script for its printed PASS marker. When tests are present, run `python -m pytest -q tests`.
