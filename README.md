# Cross-Architecture-Function-Call-Analysis
## Overview
Scripts to create architecture-independent Function Call Sequence Graph (FCSG) from IDA analysis results. The flow of FCSG image (.svg) creation is as follows.
1. Parsing binary files with IDA to create function call lists.
2. Delete functions called by all library functions with `searchlibroot.py` based on the function call lists.
3. Create an FCSG with `list2nx_ma.py`.
4. Create a svg image of FCSG with `outgraph.py`.

### 1. Parsing binary files with IDA to create function call lists
Static analysis of binary files in IDA to create a python function call list. The function call lists created by IDA is shown below.
```python
[
  ["func_1",
    ["func_1_1", "func_1_2"],
    ["func_1_2", "func_1_3"],
    ...
    ["func_1_m", "func_1_n"]],
  ["func_2",
    ["func_2_1", "func_2_2"],
    ["func_2_2", "func_2_3"],
    ...
    ["func_2_m", "func_2_n"]],
    ...
]
```
This list indicates that `func_1_2` may be called immediately after `func_1_1` inside `func_1`, and `func_1_3` may be called immediately after `func1_2` (It continues to `func_1_m`). 
The same applies to func2.
The list is stored locally using the python pickle module.

### 2. Delete functions called by all library functions with `searchlibroot.py` based on the function call lists.
Determine if `func1` or `func2` in the list is a library function, and if it is a library function, delete the internally invoked function call sequence. Save the new list to `output_path` with pickle

```
python3 searchlibroot.py output_path input_path1 [input_path2 ...]
```

### 3. Create an FCSG with `list2nx_ma.py`
FCSG creates a graph module for FCSG by receiving the path of the list in `input_path`. Networkx is used to create the graph module. The graph module and graph name are listed and saved in `output_path` using pickle.

```
python3 list2nx_ma.py output_path input_path1 [input_path2 ...]
```

### 4. Create a svg image of FCSG with `outgraph.py`
The path of the graph module is received in `input_path` and the FCSG svg image is created in `output_path`.

```
python3 outgraph.py output_path input_path1 [input_path2 ...]
```