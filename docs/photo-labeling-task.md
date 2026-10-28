# Independent photo labeling task — prepared, not launched

No Toloka account/session connector is available; no process or Windows user
`TOLOKA_TOKEN` was available. Account eligibility, credits, expert availability,
commission, total cost and turnaround remain unknown. No images were transferred,
accounts created or paid tasks launched. Obtain those facts and approval first.

Prepare eight original/permissioned holdouts: three single-scale gauges, three
dual-scale gauges (including an ambiguous example) and two unreadable examples.
Keep MAXIMATOR exploratory, outside primary scoring. A source/permission manifest,
original/submitted hashes and exact submitted-image version remain private.
There are no new photographs or fabricated ground-truth records in this task.

Reviewer input: opaque item ID plus the exact validated submitted image. Do not
show model outputs, expected answers, filenames or incident context. Collect:

- Category/readability; literal visible units and equipment label text.
- Measurement type supported by the image, or unknown; never assume DP.
- Each visible scale's unit, bounds, tick spacing and needle-tip reading interval.
- Image-specific tolerance and ambiguity/occlusion reasons; abstain when unsupported.
- External valve orientation only if observable, never proven internal condition.

Use instrument-literate reviewers qualified on scale/unit correspondence, needle
tip versus counterweight, pressure versus DP and correct abstention. Obtain two
independent human labels and qualified human adjudication; retain unresolved
ambiguity instead of forcing a numeric reference. Freeze references before model
evaluation. Visual reading references are not calibrated process measurements.

Confirm a genuinely human-only workflow in the actual account. Toloka's documented
Quorum no-review configuration has its own overlap/quality requirements; default
LLM review or synthetic labels do not meet this independent-reference protocol.
Run a small human-reviewed pilot only after permission/cost approval; actual
reviewer suitability and turnaround cannot be inferred from an export template.

Score separately, retaining every case denominator: production-contract validity;
numeric/unit agreement against frozen visual intervals; correct abstention on
ambiguous/unreadable images. Do not tune solely to the first photograph or report
contract success as accuracy. The existing [eight-photo plan](photographic-analysis.md)
does not authorize additional calls during this sprint.

Official references: [platform workflow](https://platform.toloka.ai/docs/explanation/how-the-platform-works/),
[quality controls](https://platform.toloka.ai/docs/explanation/quality-control/).
