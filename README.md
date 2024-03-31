# podgenai
Generate approximately an hour-long audio podcast mp3 on a given topic using GPT4 AI. An [OpenAI API key](https://platform.openai.com/api-keys) is required.

This very much is hurriedly-written alpha software, with a lot of work left to be done, but it is tested to work.

## Approach
For a given topic, the high-level approach is:
* The voice is selected using AI.
* A list of applicable subtopics are listed using AI.
* For each subtopic, the corresponding text and speech are generated using AI.
* The speech files are concatenated using `ffmpeg`.

## Samples
These generated samples are on [Jumpshare](https://jumpshare.com/file-sharing/mp3):
* [PyTorch](https://jmp.sh/pUNi9R3a) (2024-03-30) (default voice)
* [Advanced PyTorch](https://jmp.sh/LhwtgxJK) (2024-03-30) (default voice)
* [New York City](https://jmp.sh/PCNVwdJ4) (2024-03-30) (default voice)
* [Reverse osmosis water purification](https://jmp.sh/PJj7Ti9z) (2024-03-30)
* [Buffy the Vampire Slayer](https://jmp.sh/LnHdU6ic) (2024-03-31) (female voice)

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
