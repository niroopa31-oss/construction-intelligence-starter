# Local Column Mapper

This project provides a local column mapping model that can be used to map columns in Excel data to their respective roles without requiring an API key. The model is designed to facilitate the extraction and prediction of column roles based on the content of the data.

## Project Structure

```
local-column-mapper
├── src
│   ├── __init__.py
│   ├── model
│   │   ├── __init__.py
│   │   ├── train.py        # Logic for training the column mapping model
│   │   ├── predict.py      # Functions for loading the model and making predictions
│   │   └── saved           # Directory for saving trained models
│   │       └── .gitkeep
│   ├── features
│   │   ├── __init__.py
│   │   └── extractor.py     # Functions for extracting features from Excel data
│   ├── data
│   │   ├── __init__.py
│   │   └── dataset.py       # Functions for loading and preprocessing datasets
│   └── mapper.py            # Main entry point for column mapping functionality
├── tests
│   ├── __init__.py
│   ├── test_extractor.py     # Unit tests for feature extraction functions
│   ├── test_mapper.py        # Unit tests for mapping functionality
│   └── test_predict.py       # Unit tests for prediction functions
├── notebooks
│   └── explore_mapping.ipynb  # Jupyter notebook for exploratory data analysis
├── requirements.txt           # List of project dependencies
└── README.md                  # Project documentation
```

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd local-column-mapper
pip install -r requirements.txt
```

## Usage

1. **Training the Model**: Use the `train.py` script to preprocess your data and train the column mapping model.
2. **Making Predictions**: Use the `predict.py` script to load the trained model and perform predictions on new Excel data.
3. **Feature Extraction**: Utilize the `extractor.py` functions to extract relevant features from your input data before training or prediction.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.