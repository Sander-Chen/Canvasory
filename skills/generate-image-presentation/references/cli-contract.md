# Image PPTGen CLI contract

Contract version: `0.2.1`

## Contents

- [Commands](#commands)
- [HTTP routes](#http-routes)
- [Output and exits](#output-and-exits)

The Image CLI is a thin HTTP client. It has no workflow database and does not
import the backend. The default base URL is `http://127.0.0.1:3130`; tests and
isolated runtimes may override it with `--base-url`.

## Commands

- `image-pptgen doctor --json`
- `image-pptgen material submit --title <title> --text-file <path> --json`
- `image-pptgen split propose --deck-id <id> --json`
- `image-pptgen split revise --draft-id <id> --instruction <text> --json`
- `image-pptgen split revise --draft-id <id> --instruction <text> --allow-title-changes --json` (only for an explicit positive title or heading rename)
- `image-pptgen split revise --draft-id <id> --target-page-count <n> --json`
- `image-pptgen split confirm --draft-id <id> --json`
- `image-pptgen generate --deck-id <id> --auto --json`
- `image-pptgen generate --deck-id <id> --requirement-file <path> --json`
- `image-pptgen status --run-id <id> --follow --jsonl`
- `image-pptgen result --run-id <id> --json`
- `image-pptgen result --run-id <id> --static-preview-file <path> --json`

There are no user-selectable model, provider, renderer, config, Requirement ID,
Color, prompt, or split-mode arguments. Generation requires exactly one intent:
`--auto`, or `--requirement-file` containing the final confirmed whole-Deck
direction as UTF-8 text. The CLI reads that file without rewriting its content.
The public server selects the exact `Codex Native Image 5.0 Sol Low Director`
configuration: Sol low design director, Luna low image generator, and Sol low
palette extraction. It also owns faithful split execution.

## HTTP routes

- `GET /api/runtime-identity`
- `POST /api/decks`
- `GET /api/configs`
- `POST /api/decks/<id>/split-drafts` with `{}`
- `POST /api/deck-split-drafts/<id>/revise` with exactly one of `instruction` or
  `target_page_count`
- `POST /api/deck-split-drafts/<id>/confirm`
- `POST /api/generate` accepts exactly one of these fixed payloads. Auto:

  ```json
  {
    "deck_id": 1,
    "mode": "auto"
  }
  ```

  Manual:

  ```json
  {
    "deck_id": 1,
    "mode": "manual",
    "requirement_text": "the exact final confirmed whole-Deck direction"
  }
  ```

  The server owns `config_id`, `engine=image`, `strategy=image_5_0`, Requirement
  creation for Manual, and the empty Manual color selection. Auto uses the
  existing AutoSkill and accepts no Manual requirement text.

- `GET /api/runs/<id>/status`
- `GET /api/runs/<id>`
- `GET /api/runs/<id>/download`
- Preview: `/history/run/<id>/preview`

## Output and exits

Commands return one JSON object unless marked JSONL. Proposal and revision
return the complete Markdown projection, `draft_id`, `deck_id`, faithful mode,
page count, and status. A pure target-page revision uses the same pending draft,
does not call a model, and returns a typed `target_page_count_unavailable`
error without changing the draft when the requested count cannot be reached.
`instruction` and `target_page_count` are mutually exclusive. Confirmation
returns final slide IDs exactly once.
Generation returns one `batch_id` and one `run_ids` array containing exactly
one retained positive Run ID. Status JSONL
contains grounded `task_progress`, `current_activity`, `source_facts`, and
follow elapsed time. Result returns the existing Run status, image artifact
projection, Preview URL, and Run download URL; missing or failed pages are
never projected as successful. A completed result reads only that
Run's completed `/artifacts/` PNG routes while the local runtime is available
and writes a per-Run offline bundle under the existing artifact root. The bundle
contains ordered PNGs, `index.html`, `manifest.json`, and a matching sibling
ZIP; the viewer also has its own byte-identical ZIP copy so its download link
works from `file:`. The manifest records Run ID, page order, PNG hashes/sizes,
and ZIP hash/size. On macOS and Linux the `preview_url` and
`download_url` are the resulting `file:` viewer and ZIP URLs; they do not need
network, the backend, or port 3130 after `result` exits. In-progress Runs may
still return loopback Preview and Run download URLs.

`--static-preview-file` remains an R58-compatible optional command argument on
macOS and Linux. It writes its legacy standalone embedded-image page atomically
and returns `static_preview_path` plus `static_preview_url`; it does not create
a Run or keep the runtime alive. It is not the completed-Run interactive bundle
handoff.

Exit codes:

- `0`: success
- `2`: local input or command-contract error
- `3`: platform unavailable
- `4`: platform/API response error

Errors are one JSON object on stderr with stable `error` and `message` keys.
Unknown mutation outcomes are never automatically retried. Image material is
rejected before any platform or model request.


## Atomic generate, follow, and result handoff

On macOS and Linux, one approved `generate-and-follow` invocation performs
exactly one `generate`, one continuous same-Run `status --follow`, and, only
after successful terminal follow, one same-Run `result` readback. Its first
line is the generation receipt, intermediate lines are status JSONL, and the
final line is the result JSON. Follow or result failure preserves its native
exit status and the existing Run; generation is never retried. The caller
must not issue another result command or offer whole-Deck regeneration merely
because a separate result command was blocked.
