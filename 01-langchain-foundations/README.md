# 01 — LangChain Foundations: progressive local lab

Each committed stage below is independently runnable from this directory.
Install the pinned packages in `requirements.txt` into a Python virtual environment.
Use the locally loaded Foundry models required by each stage; no cloud key is required.

## Available concepts

1. **Model and local runtime**
   - `python src/stage_a_model.py`
2. **Prompt Template**
   - `python src/stage_b_prompt.py`
3. **Tool definition and binding**
   - `python src/stage_c_tools.py`
4. **Manual ToolMessage loop**
   - `python src/stage_d_manual_tool_loop.py`

Run the stage script for its printed PASS marker. When tests are present, run `python -m pytest -q tests`.
