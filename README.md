# Instagram Follower Analysis

This tool analyzes Instagram follower data to determine demographic information using the Perplexity API.

## Setup

1. Clone this repository
2. Edit `api_config.py` and add your Perplexity API key:
   ```python
   PERPLEXITY_API_KEY = "your_actual_api_key_here"
   ```
3. Make sure your Instagram data JSON file is available

## Usage

Run the script with the following command:

```bash
python instagram_follower_analysis.py --input path/to/instagram_data.json [--output results.json] [--human-only]
```

### Arguments:

- `--input` or `-i`: Path to JSON file with Instagram data (required)
- `--output` or `-o`: Output file path for saving results (optional)
- `--human-only`: Filter out non-human accounts (optional)
- `--api-key`: Directly provide a Perplexity API key (optional)

### API Key Options:

The script will try to find your Perplexity API key in the following order:
1. Command-line argument `--api-key`
2. Environment variable `PERPLEXITY_API_KEY`
3. The `api_config.py` file

## Example

```bash
python instagram_follower_analysis.py --input data/followers.json --output results.json --human-only
```

## Features

- Extract follower data from Instagram JSON files
- Filter out non-human accounts (businesses, organizations, etc.)
- Predict gender based on first names using gender-guesser
- Predict ethnicity/race using surname analysis from dictionary and Census data
- Save results to JSON for further analysis

## Ethnicity Classification

The tool uses a robust multi-layered approach to predict ethnicity:

1. **US Census Data**: When available, uses the official US Census surname database 
2. **Surname Dictionary**: Contains common surnames mapped to ethnic groups
3. **Partial Matching**: Detects compound surnames and variations

Supported ethnicities:
- East Asian (Chinese, Korean, Japanese, Vietnamese)
- South Asian (Indian, Pakistani, Bangladeshi, Sri Lankan)
- Hispanic/Latino
- Black/African American
- Middle Eastern
- White/European

## Usage

Run the script with a JSON file containing Instagram data:

```bash
python instagram_follower_analysis.py --input your_instagram_data.json
```

Options:
- `--input` or `-i`: Path to JSON file with Instagram data (required)
- `--output` or `-o`: Path to save output results as JSON (optional)
- `--human-only`: Filter out accounts that appear to be businesses/organizations (optional)
- `--download-census`: Download US Census surname data for improved ethnicity detection (optional)

## Example Commands

Basic usage:
```bash
python instagram_follower_analysis.py --input instagram_data.json
```

Filter for human accounts and download Census data:
```bash
python instagram_follower_analysis.py --input instagram_data.json --human-only --download-census
```

Save results to a file:
```bash
python instagram_follower_analysis.py --input instagram_data.json --output results.json
```

## JSON Format

The script expects a JSON file with Instagram data in the format shown in the example, containing a "node" object with "edge_related_profiles" data.

## Notes

- Gender prediction uses the `gender-guesser` library, which attempts to determine gender based on first names
- Ethnicity prediction uses a combination of US Census data and dictionary-based matching
- All results show the source of ethnicity prediction (census, dictionary, partial_match, or none)
- Names with special characters or emojis are normalized
- Non-human account detection looks for keywords like "store," "club," "official," etc. 