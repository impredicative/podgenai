# podgenai
**podgenai** is a Python 3.12 application to generate approximately an hour-long informational single-speaker audiobook/podcast mp3 file on a given topic using the GPT-4 LLM. A funded [OpenAI API key](https://platform.openai.com/api-keys) is required.

This very much is hurriedly-written alpha software, but it is tested to work, and the used prompts have been customized to obtain reasonable results.

## Approach
For a given topic, the high-level reference approach is:

* The voice is selected using the LLM from three choices.
* A list of applicable subtopics are listed using the LLM. If however the topic is unknown to the LLM, the process is aborted.
* Concurrently for each subtopic, the corresponding text and speech are generated using the LLM and TTS respectively.
* The speech files are concatenated using `ffmpeg`.

## Samples
These generated mp3 files are available for download. In effect, these also constitute a minimal manual test suite, with the unique purpose of each sample noted. As a reminder, the voice is selected by the LLM.

| Voice    | Name                                                                                                                                          | Purpose                                                               |
|----------|-----------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| Default  | [PyTorch](https://mega.nz/file/kEVRXSqS#J0o9wRpTxGMMH4q7_SmrPkIpUEF0VAYheMzJBTQ0L_0)                                                          | Technical content generation                                          |
| Default  | [Advanced PyTorch](https://mega.nz/file/QF10lToJ#p-Pnxy8G2sKwcPPU5TTFyelhTOSm7uHxOTlYHN-r2bA)                                                 | Advanced technical content generation                                 |
| Default  | [New York City: present and future](https://mega.nz/file/EBEVDKwJ#eqJ1gDWh2Pr0Tfw-WT1PR2bmCQjlyR_TlJYjvNTibhM)                                | Non-technical content generation                                      |
| Default  | [Artificial General Intelligence (AGI): Approaches and Algorithms](https://mega.nz/file/wNUn2JiT#-cwrVns0kciaQ3PKE9JW159jEP_6FkE9luyowXYu4kM) | Non-hierarchical flattened single-level subtopic list enforcement     |
| Female   | [Human circulatory system (unabridged)](https://mega.nz/file/9V9nHJrZ#4lm_hOYrqIUw8N-0VGcaa6zx8dwtuGRLqJLyo8pG_yE)                            | Implicit topic support for unabridged suffix, covering more subtopics |
| Female   | [Buffy the Vampire Slayer](https://mega.nz/file/AV0hQTiA#apUKjUZHwlzWLafIKZDSnVb5b0mULkqQM74a3zNYDhU)                                         | Female voice selection                                                |
| Male     | [Bitcoin for nerds](https://mega.nz/file/pZ9GiDQD#5xhPKeR1pFX73p4PJeWmFQbqBVH-dQPstLS1PDtNJV0)                                                | Male voice selection                                                  |


## Setup
* Ensure that [`rye`](https://rye-up.com/) is installed and available.
* Clone or download this repo.
* In the repo directory, run `rye sync` or more narrowly just `rye sync --no-lock` if on Linux.
* In the repo directory, create a file named `.env`, with the intended environment variable `OPENAI_API_KEY=<your OpenAI API key>`, or set it in a different way.
* Ensure that `ffmpeg` is available.
* If updating the repo, rerun `rye sync`.

## Usage
Usage can be as a command-line application or as a Python library. By default, the generated mp3 file will be written to the repo directory. As of 2024, the estimated cost per generation is under $2 USD and the time taken is under three minutes.

### Usage tips
* For a potentially longer list of covered subtopics, consider appending the "(unabridged)" suffix to the requested topic, e.g. "PyTorch (unabridged)".

### Usage as application
* To show help, run `python -m podgenai -h`.
* To run for a specified topic, use `python -m podgenai "My favorite topic"`. If a topic is not specified, you will interactively be prompted for it. 
* To specify a preexisting output directory path, use `python -m podgenai -t "My favorite topic" -p "/my/preexisting/dir"`.
* To specify an output file path, use `python -m podgenai -t "My favorite topic" -p "~/something.mp3"`.

### Usage as library
This package is not available on PyPI due to its unpolished nature, but it can nevertheless be called as a library. If successful, the output path is returned. If failed for a common reason, `None` is returned, and a relevant error is printed. As such, the return value must be checked. This section is subject to change as per Python best practices.

```python
from pathlib import Path
from podgenai import generate_media

# With default output path:
output_file_path = generate_media("My favorite topic")  # Check return value!

# With preexisting output directory path:
output_file_path = generate_media("My favorite topic", output_path=Path('/tmp'))  # Check return value!

# With output file path:
status = bool(generate_media("My favorite topic", output_path=Path('~/foo.mp3')))  # Check return value!
```

## Caching
* Text outputs are cached locally for four weeks in the `.diskcache` subdirectory.
* Audio segments are currently cached locally by the segment name in the `work` subdirectory. They can manually be deleted. This deletion is currently not automatic. Moreover, it can currently be necessary to delete them if the cache is to be bypassed.

## Disclaimer
<sub>This software is provided "as is," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.</sub>

<sub>Users should be aware that both the text and the audio of the generated files are produced by artificial intelligence (AI) based on the inputs given and the data available to the AI model at the time of generation. As such, inaccuracies, errors, or unintended content may occur. Users are advised to exercise caution and verify the accuracy and appropriateness of the generated content before any use or reliance.</sub>

<sub>You are responsible for the costs associated with the use of the OpenAI API as required by the software, and you must comply with the OpenAI API terms of service. The software's functionality is dependent on the availability and functionality of external services and software, including but not limited to the OpenAI API and ffmpeg, over which the authors have no control.</sub>

<sub>The use of the OpenAI API key and any generated content must comply with all applicable laws and regulations, including copyright laws and the terms of service of the OpenAI platform. You are solely responsible for ensuring that your use of the software and any generated content complies with the OpenAI terms of service and any other applicable laws and regulations.</sub>

<sub>This software is licensed under the GNU Lesser General Public License (LGPL), which allows for both private and commercial use, modification, and distribution, subject to the terms and conditions set forth in the LGPL. You should have received a copy of the GNU Lesser General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.</sub>

<sub>The authors do not claim ownership of any content generated using this software. Responsibility for the use of any and all generated content rests with the user. Users should exercise caution and due diligence to ensure that generated content does not infringe on the rights of third parties.</sub>

<sub>This disclaimer is subject to change without notice. It is your responsibility to review it periodically for updates.</sub>