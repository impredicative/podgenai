# podgenai
Generate about an hour-long audio podcast mp3 on a given topic.

This very much is alpha software, with a lot of work left to do, but it has been tested to work.

## Setup
* Install `rye`.
* Run `rye sync` in repo directory.
* Create `.env` file with contents `OPENAI_API_KEY=<your OpenAI API key>`.
* Ensure that `ffmpeg` is available.

## Usage
Interactively run `rye run podgenai` or `python -m podgenai`. You will be prompted for a topic of your choice.
The podcast mp3 file will be written to the repo directory. As of March 2024, the estimated cost per generation is under $2 USD.

## Samples
* [PyTorch](https://jmp.sh/s/GD0Qbz8hRix80AprAFjX)