# podgenai
**podgenai** is a Python 3.12 application to generate approximately an hour-long informational single-speaker audiobook/podcast mp3 file on a given topic using the GPT-4 LLM. A funded [OpenAI API key](https://platform.openai.com/api-keys) is required.

## Links
| Caption     | Link                                               |
|-------------|----------------------------------------------------|
| Repo        | https://github.com/impredicative/podgenai          |
| Changelog   | https://github.com/impredicative/podgenai/releases |
| Package     | https://pypi.org/project/podgenai/                 |
| Podcast     | https://podcasters.spotify.com/pod/podgenai        |
| Podcast RSS | https://anchor.fm/s/f4868644/podcast/rss           |

## Approach
The `gpt-4-0125-preview` and `tts-1` models are used. For a given topic, the high-level reference approach is:

* Applicable subtopics are listed using the LLM. If however the topic is unknown to the LLM, the process is aborted.
* The voice is selected using the LLM from four choices.
* Concurrently for each subtopic, the corresponding text and speech are generated using the LLM and TTS respectively.
* The speech files are concatenated using `ffmpeg`.

Although there may sometimes exist some semantic repetition of content across subtopics, this has intentionally not been "optimized away" because this repetition of important points can help with learning and memorization. To dive deeper into a particular subtopic, one can try to create a new file just for it.

## Samples
These generated mp3 files are available for download. In effect, these also constitute a minimal manual test suite, with the unique purpose of each sample noted. As a reminder, the voice is selected by the LLM.

There is also a related [podcast](https://podcasters.spotify.com/pod/podgenai) ([RSS](https://anchor.fm/s/f4868644/podcast/rss)) to which episodes on additional topics may be manually posted over time.

A playback speed of 1.05x is recommended for most topics.

| Voice   | Name                                                                                                                                          | Purpose                                                           |
|---------|-----------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| Default | [PyTorch](https://mega.nz/file/5Ic21CZK#ovayjipDqYeYaSw9HhRTufjIxIuJr5M8lFq3LNvtEQQ)                                                          | Technical content generation                                      |
| Default | [Advanced PyTorch](https://mega.nz/file/kFsVxSZQ#LFrQVqH-1T1uLHNtgXrjGZYdgcyiE2FCpEu1ztZx3Ak)                                                 | Advanced technical content generation                             |
| Default | [Software engineer job interview tips](https://mega.nz/file/RYtUHboC#Vf6qT_nU3ncXSymHkfmbg4jcg0CHvj020ixmS5pYlxY)                             | Default voice selection                                           |
| Emotive | [New York City: present and future](https://mega.nz/file/gEcBERqL#LCdkwFMCt2L1PdQLpD-6-BZ8VrvalTlZwqrSzNEw5Cc)                                | Non-technical content generation                                  |
| Emotive | [Living a good life](https://mega.nz/file/NNMUFTJT#8ga2REaZaT79-zf83KqBT2tUW8Q8j5sT0WAuxQUEpQ8)                                               | Emotive voice selection                                           |
| Default | [Artificial General Intelligence (AGI): Approaches and Algorithms](https://mega.nz/file/0JkWnDQQ#PSUA5aj0q_yU18T4XsazYZoSG9bqjUi7vCLmjVrY1IA) | Non-hierarchical flattened single-level subtopic list enforcement |
| Female  | [Human circulatory system (unabridged)](https://mega.nz/file/UYt2WLDA#4q-UI8cWffzN0PG8ZGiQK_96dudklBJOfFmpE_3for4)                            | Implicit topic support for unabridged suffix                      |
| Female  | [Buffy the Vampire Slayer](https://mega.nz/file/FddQWRJb#q_3XoTfgsQIvU6oZcJK7Y9or4Tjcx7BK2YLf_whjH4g)                                         | Female voice selection                                            |
| Male    | [Bitcoin for nerds](https://mega.nz/file/QVNyWYrZ#RqKuAcG6LUwOZi20ZBkygRNin9f7rpLBm1xsoILoAFI)                                                | Male voice selection                                              |

## Setup
* In the working directory, create a file named `.env`, with the intended environment variable `OPENAI_API_KEY=<your OpenAI API key>`, or set it in a different way.
* Optionally set the environment variable `PODGENAI_OPENAI_MAX_WORKERS=32` for faster generation, with its default value being 16.
* Ensure that `ffmpeg` is available.
* Continue the setup via GitHub or PyPI as below.

### Setup via GitHub
* Ensure that [`rye`](https://rye-up.com/) is installed and available.
* Clone or download this repo.
* In the repo directory, run `rye sync` or more narrowly just `rye sync --no-lock` if on Linux.
* If updating the repo, rerun the `rye sync` step.

### Setup via PyPI
* Create and activate a Python 3.12 virtual environment.
* Install via [PyPI](https://pypi.org/project/podgenai/): `pip install -U podgenai`.

## Usage
Usage can be as a command-line application or as a Python library. By default, the generated mp3 file will be written to the current working directory. As of 2024, the estimated cost per generation is under 2 USD, more specifically under 0.10 USD per subtopic. The time taken is under three minutes.

### Usage tips
* If a requested topic fails to generate subtopics, try rewording it, perhaps to be broader or narrower or more factual. Up to two attempts are made, although the first attempt will use the disk cache if available.
* For a potentially longer list of covered subtopics, consider appending the "(unabridged)" suffix to the requested topic, e.g. "PyTorch (unabridged)".
* In case the topic fails to be spoken at the start of a podcast, delete `./work/<topic>/1.*.mp3` and regenerate the output.
* To optionally generate a cover art image for your topic, [this custom GPT](https://chat.openai.com/g/g-SvmRhBwX1-podcast-episode-cover-art) can be used.

### Usage as application
* To show help, run `python -m podgenai -h`.
* To require confirmations along the way, allowing for early cancelation, use `-c`. This is recommended.
* To run for a specified topic, use `-t "My favorite topic"`. If a topic is not specified, you will interactively be prompted for it. 
* To specify a preexisting output directory path, use `-p "/my/preexisting/dir"`.
* To specify an output file path, use `-p "~/something.mp3"`.

For example, `python -m podgenai -c -t "My favorite topic" -p "~/Downloads/"`.

A nonzero exitcode exists if there is an error.

### Usage as library
When called as a function, the output file path is returned. If it fails, a subclass of the `podgenai.exceptions.Error` exception is raised.

```python
from pathlib import Path
from podgenai import generate_media

# With default output path:
output_file_path = generate_media("My favorite topic")

# With preexisting output directory path:
output_file_path = generate_media("My favorite topic", output_path=Path('/tmp'))

# With output file path:
output_file_path = generate_media("My favorite topic", output_path=Path('~/foo.mp3'))
```

## Caching
Text and speech segments are cached locally on disk in the `./work/<topic>` directory. They can manually be deleted. This deletion is currently not automatic. Moreover, it can currently be necessary to delete one or more applicable cached files if the cache is to be bypassed.

## Disclaimer
<sub>This software is provided "as is," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.</sub>

<sub>Users should be aware that both the text and the audio of the generated files are produced by artificial intelligence (AI) based on the inputs given and the data available to the AI model at the time of generation. As such, inaccuracies, errors, or unintended content may occur. Users are advised to exercise caution and verify the accuracy and appropriateness of the generated content before any use or reliance.</sub>

<sub>You are responsible for the costs associated with the use of the OpenAI API as required by the software, and you must comply with the OpenAI API terms of service. The software's functionality is dependent on the availability and functionality of external services and software, including but not limited to the OpenAI API and ffmpeg, over which the authors have no control.</sub>

<sub>The use of the OpenAI API key and any generated content must comply with all applicable laws and regulations, including copyright laws and the terms of service of the OpenAI platform. You are solely responsible for ensuring that your use of the software and any generated content complies with the OpenAI terms of service and any other applicable laws and regulations.</sub>

<sub>This software is licensed under the GNU Lesser General Public License (LGPL), which allows for both private and commercial use, modification, and distribution, subject to the terms and conditions set forth in the LGPL. You should have received a copy of the GNU Lesser General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.</sub>

<sub>The authors do not claim ownership of any content generated using this software. Responsibility for the use of any and all generated content rests with the user. Users should exercise caution and due diligence to ensure that generated content does not infringe on the rights of third parties.</sub>

<sub>This disclaimer is subject to change without notice. It is your responsibility to review it periodically for updates.</sub>