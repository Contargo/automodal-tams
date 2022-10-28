# TAMS

Sample implementation of an TAMS (thing action management system) after TASMI Specification.

## How to setup

### Prerequisites

### Development setup

If you only want to use the mqtt-sps-bridge directly, you can skip this section. Although we
can very much recommend `poetry` in general for your own python projects.

We use `poetry` to manage our dependencies. To install `poetry` you can use
[(more infos here)](https://python-poetry.org/docs/):
```shell
$ curl -sSL https://install.python-poetry.org | python -
```

Our dependencies are documented in the [pyproject.toml](pyproject.toml), the
explicit versions with hashes for the libraries you can find in
[poetry.lock](poetry.lock).


### Installation

```shell
$ poetry install
```

## Usage

All IPs defaults to ``localhost / 127.0.0.1``.

```shell
$ python src/tams/main.py
```

## Roadmap

This project has no roadmap. It is just a reference/example implementation.

