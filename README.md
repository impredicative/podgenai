# podgenai
Generate approximately an hour-long audio podcast mp3 on a given topic using GPT4.

This very much is alpha software, with a lot of work left to be done, but it is tested to work.

## Setup
* Install [`rye`](https://rye-up.com/).
* Run `rye sync` in repo directory.
* Create a file named `.env` in the repo directory, with the intended environment variable `OPENAI_API_KEY=<your OpenAI API key>`, or set it in a different way.
* Ensure that `ffmpeg` is available.

## Usage
Interactively run `rye run podgenai` or `python -m podgenai`. You will be prompted for a topic of your choice.
The podcast mp3 file will be written to the repo directory. As of 2024, the estimated cost per generation is under $2 USD.

## Caching
* Text outputs are cached locally for four weeks in the `.diskcache` subdirectory.
* Audio segments are currently cached locally by the segment name in the `work` subdirectory. They can manually be deleted. This deletion is currently not automatic. Moreover, it can currently be necessary to delete them if the cache is to be bypassed.

## Samples
These generated samples are on [Jumpshare](https://jumpshare.com/file-sharing/mp3):
* [PyTorch](https://jmp.sh/pUNi9R3a) (2024-03-30)
* [Advanced PyTorch](https://jmp.sh/LhwtgxJK) (2024-03-30)
* [New York City](https://jmp.sh/PCNVwdJ4) (2024-03-30)