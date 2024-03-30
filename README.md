# podgenai
GPT4 audio podcast generator

This very much is alpha software, but it does work.

## Setup
* Install `rye`.
* Run `rye sync` in repo directory.
* Create `.env` file with contents `OPENAI_API_KEY=<your OpenAI API key>`.
* Ensure that `ffmpeg` is available.

## Usage
Interactively run `rye run podgenai`. You will be prompted for a topic of your choice, e.g. "PyTorch" (specify without quotes).
The podcast mp3 file will be written to the repo directory. As of March 2024, the estimated cost per generation is under $2 USD.
