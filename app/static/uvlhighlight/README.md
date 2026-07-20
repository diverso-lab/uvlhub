# uvlhighlight — Syntax highlighting for Universal Variability Language in LaTeX

**Author:** José Miguel Horcas
**Email:** [horcas@uma.es](mailto:horcas@uma.es)
**License:** LaTeX Project Public License (LPPL) 1.3c

---

## Description

The `uvlhighlight` package provides syntax highlighting support for the **Universal Variability Language (UVL)** in LaTeX documents. It is built on top of the `listings` package and enables expressive and customizable formatting of UVL models.

The Universal Variability Language (UVL) is described in:

Benavides et al., *UVL: Feature modelling with the Universal Variability Language*, Journal of Systems and Software, 2025.

---

## Features

The package provides:

* Syntax highlighting for:

  * Keywords
  * Features
  * Attributes
  * Constraints
  * Strings, numbers, and comments
* Multiple visual themes:

  * Default
  * Flamapy
  * UVLS (dark mode)
  * Black & White (print-friendly)
* Inline semantic commands for UVL elements.
* Support for user-defined attributes.
* Integration with the `listings` package.
* Inclusion of external `.uvl` files.

---

## Installation

### Via CTAN / TeX distributions

The package can be installed using standard tools such as TeX Live or MiKTeX.

### Manual installation

1. Download the package

2. Place `uvlhighlight.sty` in your local TeX tree.

3. Refresh the filename database.

---

## Usage

Load the package in the preamble:

```latex
\usepackage{uvlhighlight}
```

### Minimal example

```latex
\documentclass{article}
\usepackage{uvlhighlight}

\begin{document}

\begin{lstlisting}[language=UVL]
features
    Pizza
        optional
            Cheese
\end{lstlisting}

\end{document}
```

---

## Package Options

The package supports several options to customize appearance:

* `default` — standard color theme
* `flamapy` — Flamapy-inspired colors
* `uvls` — dark theme (VS Code inspired)
* `bw` — black & white theme (print-friendly)
* `beramono` — Bera Mono font (default)
* `inconsolata` — Inconsolata font
* `nofont` — disables automatic font loading

---

## Main Commands

* `\UVL` — typesets the UVL acronym
* `\UVLKeyword{...}` — highlights keywords
* `\feature{...}` — highlights features
* `\attribute{...}` — highlights attributes
* `\constraint{...}` — formats constraint expressions
* `\uvlattributes{...}` — defines custom attributes

---

## Environments

* `lstlisting` with `language=UVL` for code blocks
* `\inputuvl` to include external `.uvl` files

---

## Documentation

Full documentation is available in:

```
uvlhighlight-doc.pdf
```

---

## Requirements

* LaTeX (pdfLaTeX, XeLaTeX, or LuaLaTeX)
* `listings` package
* Standard font encodings

---

## License

This work is distributed under the terms of the
**LaTeX Project Public License (LPPL), version 1.3c**.

https://www.latex-project.org/lppl/

---

## Changelog

### Version 1.3 (2026-04-13)

* Added `\UVL` inline command

### Version 1.2 (2026-02-16)

* Improved typography compatibility

### Version 1.1 (2025-12-02)

* Added inline commands

### Version 1.0 (2025-12-01)

* Initial release

---
