### Static Code Analyser
---
Simple static analyzer tool can find common stylistic issues in Python code. You can provide single .py file or directory with .py files and analyser will check them for compliance with the PEP standard.
### Usage
---
```sh
> python code_analyze.py <file>
```
.
### Error codes
---
After running the script, you will be asked action to perform:
* **S001** - line is too long 
* **S002** - indentation is not a multiple of four
* **S003**  - unnecessary semicolon after a statement
* **S004**  - less than two spaces before inline comments
* **S005**  - TODO found in comments
* **S006**  - more than two blank lines preceding a code line
* **S007** - too many spaces after class/name
* **S008** - class name isn't written  in CamelCase.
* **S009** - function name isn't written in snake_case.
* **S010** - argument name isn't be written in snake_case.
* **S011** - variable isn't be written in snake_case.
* **S012** - the default function/method argument value is mutable. It causes implicit errors in usage.
