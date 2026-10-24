# FT-004A: offline image-evidence probe

Offline preparation only; no account-model query or image inference was run
by the agent. The NVIDIA text integration remains separate. A successful
structured response does not grant equipment authority or establish accuracy.

## Candidate and official contract

Checked October 24, 2026:

- [Nebius public model catalog](https://tokenfactory.nebius.com/api/public/models_info)
  lists `nvidia/Nemotron-3.5-Super-VL` as active, NVIDIA, image2text, with
  image input, text output, and us-north1 region. It also has a dedicated-endpoint
  use-case tag; public listing is not a guarantee of serverless/account access.
- [Official vision example](https://docs.tokenfactory.nebius.com/api-reference/examples/vision-capabilities)
  documents URL or base64 image inputs, `messages[].content` containing text
  and `image_url` parts, and chat completions. Its older example model IDs
  are not used as evidence of current availability.
- [Chat-completion reference](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion)
  documents POST `https://api.tokenfactory.nebius.com/v1/chat/completions`.
- [Authenticated model discovery](https://docs.tokenfactory.nebius.com/api-reference/examples/list-of-models)
  documents GET `https://api.tokenfactory.nebius.com/v1/models`.

The probe uses one inline `data:image/png;base64,...` image, not a hosted URL.
It uses the shared 60-second socket timeout, 256 KiB response bound, 2048
output-token cap, no redirects, no retries, and no fallback generation.
PNG input is bounded to 64 KiB and checked against its manifest SHA-256.
The timeout is per blocking socket operation, not a whole-process deadline.
Actual account access, image acceptance, exact returned-model metadata,
reasoning/token-budget behavior, and visual accuracy remain unverified.
Do not substitute the text Nano model or silently switch models after failure.

## Evidence and fixtures

Output has exactly `readability`, `reading`, `unit`, and `evidence_ref`.
Readable evidence requires a finite JSON number and exactly `kPa`.
Unreadable evidence requires null reading AND unit. Reference must equal
the task-provided image reference. The range 0..1000 is solely a synthetic
fixture constraint, not an industrial limit. Extra fields, duplicate JSON
keys, refusal, malformed/truncated output, commands, asset assignments,
diagnosis, confidence percentages, and recovery declarations are rejected.
Asset assignment stays with the application task, never the model.

The two [synthetic fixtures](../fixtures/image-evidence/README.md) were
generated with existing Pillow 12.3.0. No dependencies were installed.
The live path uses only the standard library and pre-generated PNG bytes.
`panel-a` is the clear digital display; `panel-b` replaces the entire display
with opaque RGB pixels. Both were visually inspected in the available image
viewer. They are 480x300 PNGs with no alpha, text chunks, or other metadata.
The second contains no recoverable reading, including via transparency.
Only neutral manifest identifiers and hashes enter runtime loading. Expected
answers are in offline test/generator/documentation material, never in the
model prompt, filename, PNG metadata, or uploaded payload descriptions.

Compare returned `image_evidence` to these independent fixture expectations:
panel-a must be readable with 180 kPa and image-001; panel-b must be unreadable
with null reading/unit and image-002. CLI validation means contract validity,
not correctness of a transcription: an in-range wrong value or an invented
readable result for panel-b would fail the capability gate despite a valid
shape. Inspect both before claiming vision verification. These invented
digital fixtures do not prove arbitrary analog-gauge or real-world accuracy.

## Exact PowerShell commands (later verification only)

From a clean committed checkout in the project root:

```powershell
Set-Location 'C:\Users\surya\Projects\faulttrace'
$py = 'C:\Users\surya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py --version
& $py -m unittest discover -s tests -v
```

If needed in your Windows terminal, copy the existing Windows user environment
key to this process without displaying it. Do not paste the key into commands,
files, chat, or logs. Then perform the account discovery (no inference):

```powershell
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) {
    $env:NEBIUS_API_KEY = [Environment]::GetEnvironmentVariable('NEBIUS_API_KEY', 'User')
}
$visionAvailable = $false
$candidate = 'nvidia/Nemotron-3.5-Super-VL'
if ([string]::IsNullOrWhiteSpace($env:NEBIUS_API_KEY)) {
    Write-Output 'missing_credentials; stop before live verification'
} else {
    try {
        $catalog = Invoke-RestMethod -Method Get -Uri 'https://api.tokenfactory.nebius.com/v1/models' -Headers @{ Authorization = ('Bearer ' + $env:NEBIUS_API_KEY) } -TimeoutSec 60 -MaximumRedirection 0 -ErrorAction Stop
        $visionAvailable = @($catalog.data | Where-Object { $_.id -eq $candidate }).Count -eq 1
        Write-Output ('candidate_listed_for_account=' + $visionAvailable)
    } catch {
        Write-Output 'model_discovery_failed; stop; no automatic retry'
    }
}
```

Account listing does not prove usable billing access or successful image
inference. If the candidate is absent or discovery fails, stop and record
the blocker. Do not deploy a paid dedicated endpoint or choose a fallback.
Only after it is listed and a later live checkpoint is authorized, execute
each following invocation once. Do not rerun a failed generation automatically.

One clear-fixture request:

```powershell
if ($visionAvailable) {
    & $py -m faulttrace.image_probe --live --fixture panel-a
    Write-Output ('probe_exit_code=' + $LASTEXITCODE)
}
```

One obscured-fixture request (separate invocation; review the clear result first):

```powershell
if ($visionAvailable) {
    & $py -m faulttrace.image_probe --live --fixture panel-b
    Write-Output ('probe_exit_code=' + $LASTEXITCODE)
}
```

Offline ledger summary, including any later image attempts:

```powershell
& $py -m faulttrace.probe --ledger-summary
```

The existing gitignored `.local/nebius-usage.json` records sanitized accounting
receipts with the exact requested/returned model. No ledger redesign or
provider-response logging is added. Existing text and later image counts
share the cumulative summary; consult requested_model in the sanitized local
receipts for attribution. Model evidence, neutral fixture ID/hash, and reference
appear in sanitized CLI output; they are not added to the accounting ledger's
allowlist. Keep a sanitized CLI receipt for fixture-result provenance.
Available usage/metadata survive evidence rejection. Unknown usage stays
unknown and sums are not billing. A persistence failure yields exit 1 even
if the evidence contract passed. No website exists, so browser journey testing
is not applicable. Application integration, UI, deployment, and vision accuracy
stay open until separately verified.
