# Project coding standards for Python

1. Virtual Environments with uv:
  - Use 'uv sync' for creating virtual environments in Python projects.
  - When prompted to include a new dependency, ensure it is added to the pyproject.toml file and then update the virtual env with 'poetry lock' and using 'poetry install'.

2. Apply best-practice design patterns (e.g., DRY, SOLID).
- Always prioritize readability and clarity.
- Follow Follow the PEP 8 style guide for Python or language/framework-specific best practices
Use Version Control:

3. Running terminal commands:
- Always append the command 'rtk' when you run any terminal commands. This is used to optimize token consumption
- For example, if you want to run 'poetry install', you should run 'rtk poetry install'. if you want to run 'git pull', you should run 'rtk git pull'.

4. Unit Testing:
Always use pytest modules for unit testing. Add unit tests for functions and modules, especially in large or long-lived projects. Follow Best Practices:

5. End-to-End Testing:
- While creating and prototyping large scale projects, create end-to-end tests using pytest and follow best practises based on the chosen tool framework (Ex: PyTorch, Langchain).

6. Write clear and concise comments for each function/class. Use type hints for function arguments, variables, and return values. Ensure functions have descriptive names.

7. Do not expose applications to the public internet by default.
Implement authentication and authorization for public applications.
Vulnerability Analysis:

8. Only after the final step, Add Documentation:
All classes and functions must include docstrings.
Projects must include a README.md file.
Projects must specify dependency versions (e.g., with a lock file).