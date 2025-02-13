# Project Setup Guide

## Environment Setup

1. Create a new conda environment called 'symphony':
`conda create --name symphony python=3.10`

2. Activate the environment: `conda activate symphony`

3. Install requirements: `pip install -r requirements.txt`

# Symphony Architecture Overview

## Repository Structure

The repository is organized into the following main directories:

- `symphony/`: Main package directory containing all core components
  - `core/`: Core pipeline and interfaces
  - `embeddings/`: Embedding models and utilities
  - `discovery/`: Search and retrieval components
  - `decomposition/`: Query decomposition logic
  - `execution/`: Query execution engine
  - `utils/`: Shared utility functions

- `scripts/`: Command-line tools and utilities
  - `auto_extract_embeddings.py`: Extract embeddings from data using a GPT embedding model
  - `build_index.py`: Build search indices
  - `run_query.py`: Run queries against the system
  - `train.py`: Training a T5-based autoencoder model
  - `extract_embeddings.py`: Extracting embeddings from the trained T5-based autoencoder model

- `data/`: Data storage
  - `traindev_tables_tok/`: Tokenized table data from Open Table-and-Text Question Answering (OTT-QA)
  - `traindev_request_tok/`: Tokenized text data from Open Table-and-Text Question Answering (OTT-QA)

- `checkpoints/`: Model checkpoints for AutoEncoder embedding model
- `embeddings/`: Generated embeddings
- `index/`: Built search indices
- `tests/`: Test suite

The main interface for interacting with Symphony's components is through `core/pipeline.py`, which orchestrates the flow between different components.

## Component Overview

### Dataset (`embeddings/dataset.py`)
The `CrossModalDataset` class handles both tabular and text data, providing a unified interface for loading and preprocessing data. It supports loading from directories and serializing items into a format suitable for embedding.

### Embedding (`embeddings/`)
Symphony implements two embedding approaches:
- `AutoEmbedder`: Uses OpenAI's embedding models (text-embedding-3-small by default) for production use
- `SymphonyAutoEncoder`: A custom T5-based autoencoder model for research and offline use

### Discovery (`discovery/`)
The discovery component implements semantic search using vector indices. It combines both semantic similarity and keyword matching for improved retrieval, with configurable boosting of keyword matches.

### Decomposition (`decomposition/`)
The decomposer breaks down complex queries into simpler sub-queries that can be executed independently. It uses OpenAI's API for natural language understanding and query planning.

### Execution (`execution/`)
The executor processes decomposed queries against the retrieved context. It handles both direct lookups and more complex reasoning tasks using the OpenAI API.

### Aggregation (`execution/aggregator.py`)
The aggregator combines results from multiple sub-queries into a coherent final response, ensuring consistency and handling any conflicts in the intermediate results.

# Running Main

```
python main.py --config config.yaml "your query here"
```