# podgenai
**podgenai** is a Python 3.12 application to generate approximately an hour-long informational audiobook podcast mp3 file on a given topic using the GPT-4 LLM. A funded [OpenAI API key](https://platform.openai.com/api-keys) is required.

This very much is hurriedly-written alpha software, but it is tested to work, and the used prompts have been customized to obtain reasonable results.

## Approach
For a given topic, the high-level reference approach is:

* The voice is selected using the LLM from three choices.
* A list of applicable subtopics are listed using the LLM. If however the topic is unknown to the LLM, the process is aborted.
* Concurrently for each subtopic, the corresponding text and speech are generated using the LLM and TTS respectively.
* The speech files are concatenated using `ffmpeg`.

## Samples
These generated mp3 files can be downloaded from Mega. In effect, these also constitute a test suite, with the unique purpose of each sample noted. As a reminder, the voice is selected by the LLM.

| Voice    | Name                                                                                     | Purpose                               |
|----------|------------------------------------------------------------------------------------------|---------------------------------------|
| Default  | [PyTorch](https://mega.nz/file/kEVRXSqS#J0o9wRpTxGMMH4q7_SmrPkIpUEF0VAYheMzJBTQ0L_0)            | Technical content generation          |
| Default  | [Advanced PyTorch](https://mega.nz/file/QF10lToJ#p-Pnxy8G2sKwcPPU5TTFyelhTOSm7uHxOTlYHN-r2bA)      | Advanced technical content generation |
| Default  | [New York City: present and future](https://mega.nz/file/EBEVDKwJ#eqJ1gDWh2Pr0Tfw-WT1PR2bmCQjlyR_TlJYjvNTibhM) | Non-technical content generation      |
| Female   | [Buffy the Vampire Slayer](https://mega.nz/file/AV0hQTiA#apUKjUZHwlzWLafIKZDSnVb5b0mULkqQM74a3zNYDhU)        | Female voice selection                |
| Male     | [Bitcoin for nerds](https://mega.nz/file/pZ9GiDQD#5xhPKeR1pFX73p4PJeWmFQbqBVH-dQPstLS1PDtNJV0)               | Male voice selection                  |


## Setup
* Install [`rye`](https://rye-up.com/).
* Clone the repo.
* Run `rye sync` in the repo directory.
* Create a file named `.env` in the repo directory, with the intended environment variable `OPENAI_API_KEY=<your OpenAI API key>`, or set it in a different way.
* Ensure that `ffmpeg` is available.
* If updating the repo, rerun `rye sync`.

## Usage
Interactively run `rye run podgenai` or `python -m podgenai`. You will be prompted for a topic of your choice.
The generated mp3 file will be written to the repo directory. As of 2024, the estimated cost per generation is under $2 USD and the time taken is under three minutes. 

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