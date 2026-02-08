# BAMSec Transcript Downloader

Downloads the most recent earnings call transcripts from your BAMSec account as PDFs. Just type a stock ticker and it grabs the 8 most recent transcripts.

## What You Need

- A computer with **Python 3** installed ([download here](https://www.python.org/downloads/))
- A **paid BAMSec subscription** (free trials have limited transcript access)

## First-Time Setup (do this once)

1. Open your terminal (Mac: search "Terminal" in Spotlight / Windows: search "Command Prompt")
2. Navigate to this folder: `cd path/to/PublicAnalysis`
3. Run the setup script:
   ```
   ./setup.sh
   ```
4. Create a file called `.env` in this folder (right next to this README) with your BAMSec login:
   ```
   BAMSEC_EMAIL=your_email@example.com
   BAMSEC_PASSWORD=your_password
   ```

## How to Use

Open your terminal, go to this folder, and run:

```
./run.sh RH
```

Replace `RH` with whatever stock ticker you want. The transcripts will be saved as PDFs in a `downloads/` folder.

### More Examples

```
./run.sh AAPL       # Download 8 transcripts for Apple
./run.sh MSFT 4     # Download only 4 transcripts for Microsoft
./run.sh GOOG       # Download 8 transcripts for Google
```

## Where Do the PDFs Go?

They get saved to: `downloads/TICKER/` (e.g., `downloads/RH/`)

## Troubleshooting

- **"Credentials not found"** — Make sure you created the `.env` file with your email and password
- **"No transcripts found"** — The ticker might not have transcripts on BAMSec, or the site layout may have changed
- **Browser pops up and does nothing** — BAMSec may have changed their website. Open an issue and we'll update the script
