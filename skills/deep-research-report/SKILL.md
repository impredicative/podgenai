---
name: deep-research-report
description: Produce a comprehensive, referenced deep-research report on a given topic as a downloadable markdown file. Use when asked for a deep-research report.
---

# Deep research report

Produce a comprehensive deep-research report on the given topic.

Unless there are ambiguities that must be clarified, proceed with the deep research.

Do not provide an initialization note, progress updates, planning notes, meta-commentary, or task-status comments before, during, or after report. The user will just wait until the report becomes ready.

More detail and a longer report are typically better, so take your time.

Claims and statements in the report must individually be backed by good references. Synthesis is acceptable when it is high value and high confidence.

Do not write the report in the chat. Instead, provide it for download in a downloadable markdown file. The downloaded report file is to be a formal deliverable that will be shared with many users, so it definitely must never contain any commentary pertaining to the research request.

If the user later requests a subsequent report, the same instructions apply as for the initial report, and it too must be a downloadable markdown file.

## Structuring references

Unless otherwise requested, generate and format references in this portable reference-link style as below:

- Assign each distinct source URL a document-local ID: `S001`, `S002`, etc. Reuse its ID whenever citing it again.
- Place citations beside the supported claim: `[S001]`. Separate multiple citations with spaces: `[S001] [S002]`.
- End with a `## References` section containing visible entries: `- **S001** — Publisher. [Source title][S001].` Include dates or explanatory notes here when relevant.
- After the entries, leave a blank line and list the URL definitions. Each definition must be unindented, on one line, and contain only `[ID]: URL`.
- Every cited ID must have both a visible source entry and exactly one URL definition.
- Do not use footnotes (`[^id]`) or tool-specific citation markers.

This approach allows for correct formatting of the references when auto-converting the markdown file to a PDF file using `md-to-pdf`.

### Representative good example for this workflow

```markdown
The source supports this claim. [S001]

## References

- **S001** — Example Publisher. [Example source title with year][S001].

[S001]: https://example.com/source
```

### Representative bad example for this workflow

Footnotes style:
```markdown
The source supports this claim.[^source]

[^source]: [Example source title](https://example.com/source).
```

Descriptions placed inside URL definitions, or citations grouped into an undefined label:
```markdown
The sources support this claim. [S001, S002]

[S001]: Example Publisher. [Example source title](https://example.com/source).
```

## Follow-up commands

After the report is made available to the user, the user is free to issue one or more follow-up commands:
* CHK: Upon receiving this command, you are to check and cross-examine your generated report against the original request to see if there were any subtopics that were not reasonably addressed. If there are then any such subtopics, you are to output a supplemental new request to get only these leftover subtopics investigated, not what you already duly addressed in the report.
* GEN: This can often follow a CHK command. Upon receiving this command, you are to generate a supplemental new report against the new request.
* MRG: This can follow the CHK and GEN commands. Upon receiving this command, you are to merge the original report and the supplemental report, producing a sensibly and systematically merged report.
