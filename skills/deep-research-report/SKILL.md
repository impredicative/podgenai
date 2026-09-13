---
name: deep-research-report
description: Produce a comprehensive, referenced deep-research report on a given topic as a downloadable markdown file. Use when asked for a deep-research report or for its CHK, GEN, or MRG follow-up commands to check coverage, generate a supplemental report, or merge reports.
---

# Deep research report

Produce a comprehensive deep-research report on the given topic.

Unless there are ambiguities that must be clarified, proceed with the deep research.

Do not provide an initialization note, progress updates, planning notes, meta-commentary, or task-status comments before, during, or after report. The user will just wait until the report becomes ready.

More detail and a longer report are typically better, so take your time.

Claims and statements in the report must individually be backed by good references. Synthesis is acceptable when it is high value and high confidence.

Do not write the report in the chat. Instead, provide it for download in a downloadable markdown file. The downloaded report file is to be a formal deliverable that will be shared with many users, so it definitely must never contain any commentary pertaining to the research request.

---

Follow-up commands:

After the report is made available to the user, the user may issue one or more follow-up commands:
* CHK: Upon receiving this command, you are to check and cross-examine your generated report against the original request to see if there were any subtopics that were not reasonably addressed. If there are then any such subtopics, you are to output a supplemental new request to get only these leftover subtopics investigated, not what you already duly addressed in the report.
* GEN: This can often follow a CHK command. Upon receiving this command, you are to generate a supplemental new report against the new request.
* MRG: This can follow the CHK and GEN commands. Upon receiving this command, you are to merge the original report and the supplemental report, producing a sensibly and systematically merged report.
