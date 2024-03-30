# podgenai
Generate approximately an hour-long audio podcast mp3 on a given topic using GPT4.

This very much is alpha software, with a lot of work left to be done, but it is tested to work.

## Setup
* Install [`rye`](https://rye-up.com/).
* Run `rye sync` in repo directory.
* Create `.env` file with contents `OPENAI_API_KEY=<your OpenAI API key>`.
* Ensure that `ffmpeg` is available.

## Usage
Interactively run `rye run podgenai` or `python -m podgenai`. You will be prompted for a topic of your choice.
The podcast mp3 file will be written to the repo directory. As of March 2024, the estimated cost per generation is under $2 USD.

## Samples
These samples are shared on [Jumpshare](https://jumpshare.com/file-sharing/mp3):
* [PyTorch](https://jmp.sh/s/GD0Qbz8hRix80AprAFjX) (generated 2024-03-30)
* [New York City](https://jmp.sh/PCNVwdJ4) (generated 2024-03-30)