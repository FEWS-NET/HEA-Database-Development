# Current Experiments

**hea_documentation_QA_bot.py** ; initial proof of concept of an HEA/LIAS "chatbot" agent, designed to answer questions by referencing its knowledge base of HEA documentation. The goal is to integrate this with other tools.

**formula_translator.ipynb** ; more of a "black box" approach. The idea is to leverage an LLM to translate Excel formulas to Python code without worrying about contextual understanding, so that later we can have another agent reason over the raw Python code to infer logical groupings for class methods.

**workbook_context_extraction.ipynb** ; repurposes some of the logic from the ill fated **narrative_explanation.ipynb**, but with a simpler goal: capture text content found in the workbook alongside relevant metadata.

# TO-DO

Orchestrate the tools described above. A potential workflow I intend to explore is:

- Recurse on a given cell
- For each leaf node (or collapsed range), refer to the extracted workbook context to identify relevant text (headers, explanatory text, etc.)
- Use the result of the previous step to create context-aware variable names/named ranges
- Reconcile these variable/range names with the formulas translated into Python code
- Synthesize results into meaningful Python class structures   

# Experiment Graveyard

**graph_visualizer** ; a Flask app where you can upload an Excel workbook, enter a sheet name and cell, and it'll build and display the dependency graph. Helpful for initial exploration, but not particularly actionable.

**llm_formula_reccurse.py** ; a tool to aid in building text descriptions for different workbook cells/ranges. For a given cell, it recurses and asks for a text description of any cells not already in its cache. More actionable than the graph visualizer, but still demands a nontrivial amount of manual effort. Much of the logic here was repurposed in the **formula_translator**.

**narrative_explanation.ipynb** An attempt at associating context with cells (i.e., tagging a cell with its nearest table header), collapsing large range operations to a descriptive 'motif', and passing the enriched cell information to an LLM to get a natural language explanation of the flow of logic. This got messy pretty fast, and generated narrative summaries weren't particularly actionable for porting algorithmic logic. 
