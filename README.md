# podgenai
**podgenai** is a Python 3.14 application to generate an informational single-speaker or two-speaker audiobook/podcast mp3 file on a given topic using an OpenAI LLM. The material is generated from the model's internal knowledge or otherwise from a given markdown source document. Web search or other sources are not used. The output file is generated as a series of sections, each covering a subtopic of the given topic. A funded [OpenAI API key](https://platform.openai.com/api-keys) is required.

The loosely targeted duration of the generated file is an hour, although comprehensive coverage often results in a multi-hour duration by default. A smaller duration can in practice be enforced by limiting the number of sections to as few as three, although this is expected to result in less comprehensive coverage of the topic. For a ten hour podcast, the heuristic for its cost is $10 USD, with much of this cost being for the TTS generation, with a smaller duration costing proportionally less.

Although there might sometimes exist some semantic repetition of content across subtopics, this has intentionally not been optimized away because this repetition of important points can help with learning and memorization.

## Links
| Caption     | Link                                                 |
|-------------|------------------------------------------------------|
| Repo        | https://github.com/impredicative/podgenai            |
| Changelog   | https://github.com/impredicative/podgenai/releases   |
| Package     | https://pypi.org/project/podgenai                    |
| Podcast     | https://open.spotify.com/show/0WayD9YdeSTxcfm63lnam5 |
| Podcast RSS | https://anchor.fm/s/f4868644/podcast/rss             |

## Approach

For a given topic, the high-level generation approach is as follows:

1. Applicable subtopics are listed using the LLM. If, however, the topic is unknown to the LLM or is not supported by a given source document, the process is aborted with an explanatory error.
2. The required voice or voices are selected using the LLM from the configured choices. For a monologue, a single voice is selected; for a duologue, a male and a female voice are selected.
3. Concurrently for each subtopic, the corresponding monologue text is generated using the LLM. If a source document was provided, it is used for each generation.
4. For a duologue, concurrently for each subtopic, the corresponding duologue text and tone instructions are generated using the LLM from the subtopic's monologue text.
5. Speech is generated using text-to-speech (TTS): concurrently for each subtopic in a monologue, or concurrently for each line in a duologue.
6. The speech files are concatenated using `ffmpeg`, with appropriate pauses added between parts and subtopics, as well as between lines for a duologue.


### Models used
* `gpt-5.6-sol` is used for monologue text generation if the episode is to be created from the model's internal knowledge. It also is always used for listing subtopics and for duologue text generation.
* `gpt-5.6-terra` is used for monologue text generation if the episode is to be created from a given markdown source document.
* `gpt-4o-mini-tts-2025-12-15` is used for speech generation.

## Samples
These generated mp3 files are available for download:

| Type | Voice(s) | Name | Links |
|------|----------|------|-------|
| two-speaker from model | modern-female (marin), modern-male (cedar) | Grand Turk for cruise tourists | [Mega](https://mega.nz/file/FE81QRzY#PIAoDOkfPoTWBJBCZg9PNq4YpGd4kfVUnZt5uaC4hJw), [Spotify](https://creators.spotify.com/pod/profile/podgenai/episodes/Grand-Turk-for-cruise-tourists-e3nv758) |
| two-speaker from source | modern-female (marin), modern-male (cedar) | Indoor Carbon Dioxide and Health | [Mega](https://mega.nz/file/tNMjiD6I#UJtHW9_7q8f8cH8ImHldM6dIcKf1pGTDxvl7wjYQi3w), [Spotify](https://creators.spotify.com/pod/profile/podgenai/episodes/Indoor-Carbon-Dioxide-and-Health-e3o1vu9) |
| one-speaker from model | modern-female (marin) | New York City tourism: What's new | [Mega](https://mega.nz/file/VJ1WRbxZ#62PvDAD0ttO7JD3l9CywICB2KAMUhxLc6Jed7WkE3B4), [Spotify](https://creators.spotify.com/pod/profile/podgenai/episodes/New-York-City-tourism-Whats-new-e3njmjn) |
| one-speaker from model | modern-male (cedar)   | Writing a Will | [Mega](https://mega.nz/file/gE0EzKBT#Qm72FWa36joj_qFP7MlN2pyESLa0dS4Q6xiKwRIpLUY), [Spotify](https://creators.spotify.com/pod/profile/podgenai/episodes/Writing-a-Will-e3njm2g) |

There also is a related [podcast](https://podcasters.spotify.com/pod/podgenai) ([RSS](https://anchor.fm/s/f4868644/podcast/rss)) to which episodes may be posted over time.

A playback speed of 1.05x is recommended for non-technical topics, 1.0x for technical topics, and 0.95x for foreign language topics.

## Setup

### Common setup
* In the working directory, create a file named `.env`, with the intended environment variable `OPENAI_API_KEY=<your OpenAI API key>`, or set it in a different way.
* In `.env`, optionally also set the environment variable `PODGENAI_OPENAI_MAX_WORKERS=32` for faster generation, with its default value being 16.
* Ensure that `ffmpeg` and `ffprobe` are available. This is automatic if using the included devcontainer definition.
* Continue the setup via GitHub or PyPI as below.

### Setup via GitHub using devcontainer (recommended)
* Continue from the common setup steps.
* Clone or download this repo.
* Build and provision the defined devcontainer.

### Setup via GitHub manually
* Continue from the common setup steps.
* Clone or download this repo.
* Ensure that [`uv`](https://docs.astral.sh/uv/#installation) is installed and available.
* In the repo directory, run `uv sync --locked` to set up the environment. Alternatively, run `./scripts/setup_uv.sh` to both install `uv` and run the sync command.

### Setup via PyPI
* Continue from the common setup steps.
* Create and activate a Python 3.14 devcontainer or virtual environment.
* Install via [PyPI](https://pypi.org/project/podgenai): `pip install -U podgenai` or `uv add -U podgenai` or `uv pip install -U podgenai`.

## Usage
Usage can be as a command-line application or as a Python library. By default, the generated mp3 file will be written to the current working directory.

### Usage tips
* If a requested topic fails to generate subtopics due to a refusal, retry up to a few times, as it may succeed with several attempts. If it doesn't, try rewording it, perhaps to be broader or narrower or more factual. Up to two attempts are made per run, although the first attempt will reuse the disk cache if available.
* To control the resulting duration, specify the target number of covered subtopics using the `--max-sections` (`-s`) option.
* To switch from the default two-speaker generation to single-speaker generation, use the `--speakers` (`-k`) option.
* To optionally generate a cover art image for your topic, [this custom GPT](https://chat.openai.com/g/g-SvmRhBwX1-podcast-episode-cover-art) can be used.
* To attempt generation in a foreign language, specify the title in the desired language along with a parenthesized prefix of the language name, e.g. "México (Español)". If the generation is refused the first time, try again. Also refer to and use the `--no-markers` (`-nm`) option.

### Source document usage
It is not necessary to provide a source document for common topics because the LLM has considerable internal knowledge of them. If a source document is to be used, it must be a text or markdown file specified using the `--document` (`-d`) option. It is suggested that the source document be a detailed report on the topic, such as an exhaustive deep-research report. For those with a ChatGPT subscription, a custom GPT can be for example be created and used to generate such a downloadable report using [this definition](https://gist.github.com/impredicative/d270fe8cea8edf295f90ffde6fdd4fec).

Multiple source documents are not supported, but can first be consolidated by an LLM into a single document. A binary file such as PDF or DOCX is not supported either, but can first be converted to markdown using a tool or an LLM.

### Usage as application
Usage help is copied below:
```
$ podgenai -h
Usage: podgenai [OPTIONS]

  Generate and write an audiobook podcast mp3 file for the given topic to the given output file path.

Options:
  -t, --topic TEXT                Topic. If not given, the user is prompted for it.
  -p, --path PATH                 Output file or directory path. If an intended file path, it must have an ".mp3"
                                  suffix. If a directory, it must exist, and the file name is auto-determined. If not
                                  given, the output file is written to the current working directory with an auto-
                                  determined file name.
  -d, --document PATH             Path to a single text or markdown document file to use as the exclusive source for
                                  the podcast. If not given, the podcast is generated from the model's internal
                                  knowledge.
  -s, --max-sections INTEGER RANGE
                                  Maximum number of sections, between 3 and 100. If not given, it is unrestricted.
                                  [3<=x<=100]
  -k, --speakers INTEGER RANGE    Number of speakers, either 1 or 2. If not given, it is 2.  [1<=x<=2]
  -m, --markers / -nm, --no-markers
                                  Include markers at the start or end of sections in the generated audio. If
                                  `--markers`, markers are included, and this is the default. If `--no-markers`,
                                  markers are excluded, as can be appropriate for foreign-language generation.
  -c, --confirm / -nc, --no-confirm
                                  Confirm before full-text and speech generation. If `--confirm`, a confirmation is
                                  interactively sought as each step of the workflow progresses, and this is the
                                  default. If `--no-confirm`, the full-text and speech are generated without
                                  confirmations.
  -h, --help                      Show this message and exit.
```

Usage examples:

    $ podgenai -t "The Quest for Infinity"

    $ podgenai -t "The Quest for Infinity" -p ~/Documents/

    $ podgenai -t "The Quest for Infinity" -p ~/Documents/output.mp3 -nc

    $ podgenai -t "The Quest for Infinity" -s 3 -k 1

    # podgenai -t "The Quest for Infinity" -d ~/Downloads/deep-research_report.md

    $ podgenai -t "La Quête de l’infini (Français)" -nm

### Usage as library
```python
>>> from podgenai import generate_media
>>> help(generate_media)
```
```text
Help on function generate_media in module podgenai.podgenai:

generate_media(
    topic: str,
    *,
    output_path: Path | None = None,
    document: str | None = None,
    max_sections: int | None = None,
    speakers: int = 2,
    markers: bool = True,
    confirm: bool = False
) -> Path
    Return the output path after generating and writing an audiobook podcast to file for the given topic.

    Params:
    * `topic`: Topic.
    * `output_path`: Output file or directory path.
        If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined.
        If not given, the output file is written to the repo directory with an auto-determined file name.
    * `document`: Contents of a single text or markdown document to use as the exclusive source for the podcast.
        If not given, the podcast is generated from the model's internal knowledge.
    * `max_sections`: Maximum number of sections to generate. It is between 3 and 100. It is unrestricted if not given.
    * `speakers`: Number of speakers, either 1 or 2. Its default is 2.
    * `markers`: Include markers at the start or end of sections in the generated audio.
        If true, markers are included. If false, markers are excluded, as can be appropriate for foreign-language generation. Its default is true.
    * `confirm`: Confirm before full-text and speech generation.
        If true, a confirmation is interactively sought after generating and printing the list of subtopics, before generating the full-text, and also before generating the speech. Its default is false.

    If failed, a subclass of the `podgenai.exceptions.Error` exception is raised.
```

## Cache
Text and speech segments are cached locally on disk in the `./work/<topic>` directory. They can manually and selectively be deleted. This deletion is not automatic. Moreover, it is necessary to delete one or more applicable cached files to force a regeneration, although a change of runtime settings forces it as well, as do routine updates to the software.

## Disclaimer
<sub>This software is provided "as is," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.</sub>

<sub>Users should be aware that both the text and the audio of the generated files are produced by artificial intelligence (AI) based on the inputs given and the data available to the AI model at the time of generation. As such, inaccuracies, errors, or unintended content may occur. Users are advised to exercise caution and verify the accuracy and appropriateness of the generated content before any use or reliance.</sub>

<sub>You are responsible for the costs associated with the use of the OpenAI API as required by the software, and you must comply with the OpenAI API terms of service. The software's functionality is dependent on the availability and functionality of external services and software, including but not limited to the OpenAI API and ffmpeg, over which the authors have no control.</sub>

<sub>The use of the OpenAI API key and any generated content must comply with all applicable laws and regulations, including copyright laws and the terms of service of the OpenAI platform. You are solely responsible for ensuring that your use of the software and any generated content complies with the OpenAI terms of service and any other applicable laws and regulations.</sub>

<sub>This software is licensed under the GNU Lesser General Public License (LGPL), which allows for both private and commercial use, modification, and distribution, subject to the terms and conditions set forth in the LGPL. You should have received a copy of the GNU Lesser General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.</sub>

<sub>The authors do not claim ownership of any content generated using this software. Responsibility for the use of any and all generated content rests with the user. Users should exercise caution and due diligence to ensure that generated content does not infringe on the rights of third parties.</sub>

<sub>This disclaimer is subject to change without notice. It is your responsibility to review it periodically for updates.</sub>
