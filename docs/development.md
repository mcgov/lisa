# Development Guideline

This document describes the existing developer tooling we have in place (and what to
expect of it), as well as our design and development philosophy.

- [Understand LISA](#understand-lisa)
- [Environment Setup](#environment-setup)
  - [Visual Studio Code](#visual-studio-code)
  - [Emacs](#emacs)
  - [Other setups](#other-setups)
- [Code guideline](#code-guideline)
  - [Naming Conventions](#naming-conventions)
  - [Code checks](#code-checks)

## Understand LISA

It depends on your contribution to LISA, you may need to learn more about LISA. Learn more from the topics below.

- [Concepts](concepts.md) includes design considerations, how components work together.
- [Extensions](extension.md) includes all extendable components, and how to develop extensions in LISA.
- [How to write test cases](write_case.md) introduce the guideline to write test cases.

## Environment Setup

Follow the [instal](install.md) steps to prepare the source code. Then follow the steps below to set up the corresponding development environment.

### Visual Studio Code

First, click on the Python version at the bottom left and enter the path where the above command was issued. This will point the Code to the Poetry virtual environment.

Make sure below settings are in root level of `.vscode/settings.json`.

```json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.pylintEnabled": false,
    "editor.formatOnSave": true,
    "python.linting.mypyArgs": [
        "--strict",
        "--namespace-packages",
        "--show-column-numbers"
    ],
    "python.sortImports.path": "isort",
    "python.analysis.useLibraryCodeForTypes": false,
    "python.analysis.autoImportCompletions": false,
    "files.eol": "\n",
}
```

### Emacs

Use the [pyvenv](https://github.com/jorgenschaefer/pyvenv) package:

```emacs-lisp
(use-package pyvenv
  :ensure t
  :hook (python-mode . pyvenv-tracking-mode))
```

Then run `M-x add-dir-local-variable RET python-mode RET pyvenv-activate RET <path/to/virtualenv>` where the value is the path given by the command above. This will create a `.dir-locals.el` file as follows:

```emacs-lisp
;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")

((python-mode . ((pyvenv-activate . "~/.cache/pypoetry/virtualenvs/lisa-s7Q404Ij-py3.8"))))
```

### Other setups

- Install and enable [ShellCheck](https://github.com/koalaman/shellcheck) to find bash errors locally.

## Code guideline

### Naming Conventions

Please read the [naming conventions](https://www.python.org/dev/peps/pep-0008/#naming-conventions) section of PEP 8, which explains the meaning of each of the styles. A brief overview of the most important parts:

- Modules (and files) should use lowercase short names.
- Class (and exception) names should use the `CapWords` convention (also known as `CamelCase`)
- Function and variable names should use lowercase letters, and words should be separated by underscores to improve readability (also called `snake_case`).
- To avoid conflicts with the standard library, you can add an underscore, such as `id_`.
- Leading lines such as `_data` apply to non-public methods and instance variables. Subclasses can use it. If you don't use it in a subclass, use it like `__data` in a superclass.
- If there is a pair of `get_x` and `set_x` methods without additional parameters, please use the built-in `@property` decorator to convert them to properties.
- Constants should be similar to `CAPITALIZED_SNAKE_CASE`.
- When importing a function, try to avoid renaming it with `import as` because it introduces cognitive overhead to keep track of another name. If the name conflicts, please use the package name as the namespace, such as `import schema`, and use it as `schema.Node`.

If in doubt, follow existing conventions or check the style guide.

### Code checks

If the development environment is set up correctly, the following tools will automatically check the code. If there is any problem with the development environment settings, please feel free to submit an issue to us or create a pull request for repair. You can also run the check manually.

- [Black](https://github.com/psf/black), the opinionated code formatter resolves all disputes about how to format our Python files. This will become clearer after following [PEP 8](https://www.python.org/dev/peps/pep-0008/) (official Python style guide).
- [Flake8](https://flake8.pycqa.org/en/latest/) (and integrations), the semantic analyzer, used to coordinate most other tools.
- [isort](https://timothycrosley.github.io/isort/), the `import` sorter, it will automatically divide the import into the expected alphabetical order.
- [mypy](http://mypy-lang.org/), the static type checker, which allows us to find potential errors by annotating and checking types.
- [rope](https://github.com/python-rope/rope), provides completion and renaming support for pyls.
