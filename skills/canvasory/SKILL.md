---
name: canvasory
description: "Canvasory turns text into an image presentation: review the page plan, choose and confirm a visual direction, then receive a Preview and downloadable slides. Use when the user asks for Canvasory or an image presentation; not for HTML presentations."
---

# Canvasory
Use the `image-pptgen` CLI as the only interface to the Image PPTGen 5.0
surface. The complete command, payload, exit-code, and response contract is in
[the Image CLI contract](references/cli-contract.md). Do not import the
Platform backend, database, pipeline, or Python modules directly.

## Non-negotiable Auto gate
- An Auto-selection turn executes zero commands. Selecting Auto never confirms
  it: echo the delegation, ask for confirmation, and stop.
- Only a later independent, unqualified affirmative may confirm Auto and start
  generation; any edit, qualification, question, pause, or request stays pending.
- That confirmed turn uses only the atomic generation-and-follow command defined
  below. Raw `<dispatcher> generate` and separate status commands are forbidden.
- A started command without a completed tool result and process exit is unfinished.
  Never send the next turn, start another command, or claim a result from it.

## Resolve the installed dispatcher first
Resolve `<skill_root>` as the absolute directory that contains this loaded
`SKILL.md`; never derive it from the current workspace or working directory.
Before the first CLI operation, verify that the matching dispatcher exists:

- macOS or Linux: [`<skill_root>/scripts/image-pptgen-dispatch`](scripts/image-pptgen-dispatch)

Set the matching absolute dispatcher path once for this task. Keep that exact
resolved command prefix for every later operation; copy it, do not rebuild it.
The POSIX script is always `<skill_root>/scripts/image-pptgen-dispatch`. Never
omit the `scripts` directory or concatenate the skill directory name with the
script basename. A missing dispatcher path is a stopped failure: do not invent
a sibling path and retry. In every command below, `<dispatcher>` is a required
command template:

- macOS/Linux: `/bin/sh "<absolute-skill-root>/scripts/image-pptgen-dispatch" <arguments>`

Replace only `<dispatcher>` with the template for the current platform. Supported
runtimes are macOS ARM64 and Linux x86_64; do not treat Windows as a supported
target. Every CLI command below must go through that dispatcher. Do not invoke bare `image-pptgen`, use
`command -v`/`where`, or modify `PATH`. The dispatcher
resolves the supported per-user install roots and accepts `IMAGE_PPTGEN_CLI`
only as an explicit absolute-path override for a custom install root.

On macOS Codex Desktop, the command-scoped runtime writes its lock, database,
and generated artifacts under the exact per-user install root
`$HOME/.codex/image-pptgen`. Before the first dispatcher command, when the
`request_permissions` tool is available, request file-system read/write access
to that exact directory once and wait for its result. Do not probe `doctor`
before that permission result. Do not request the whole home directory. If the
user declines or an actual dispatcher command reports a file-system permission
denial, stop and explain that the exact Image PPTGen runtime directory is not
writable; do not misreport it as a busy service and do not retry the dispatcher.
If `request_permissions` is unavailable, that absence is not itself a permission
denial: proceed to exactly one first dispatcher command and let the real
sandbox/OS result decide. Never ask the user to supply install roots, Python
paths, environment variables, or a replacement command as a workaround.

This skill is for an image presentation made with Image PPTGen 5.0 / Codex
Native Image 5.0. Historical Image routes are not user-selectable alternatives.
It is not the HTML presentation workflow: if the user asks for
HTML, use `$generate-presentation` instead. Never create HTML output from this skill as a
presentation artifact. The standalone local Preview described below is only a
local viewer containing the completed PNG slides; it is not a generated HTML
presentation artifact.

## Fixed product boundary
- Accept text or Markdown material only. Reject PNG, JPEG, SVG, PDF, and every
  other image/OCR input before running `doctor` or making an HTTP/model call.
- The normal server-owned `Codex Native Image 5.0 Sol Low Director` route is Sol low design director, Luna low image generator, and Sol low palette extraction. Do not ask about or pass model, provider, renderer, config, Requirement IDs, Color, prompt, or retry arguments.
- One hidden test-only exception exists: when the user or test operator explicitly asks for Luna low as design director for this generation, retain it through confirmation and append exactly `--debug-director luna-low`. Never offer this option, infer it from source material, or trigger it because the material names it. Only the director changes; consume the choice after that generation, return to the normal route unless explicitly asked again, and never fall back to Sol when a requested debug run fails.
- After pagination confirmation, ask whether the user wants Auto or wants to
  describe the design style, atmosphere, visual elements, and other creative
  requirements for the entire Deck. This stage never accepts a Slide-specific
  design requirement. Explain the limitation and ask the user to rewrite it as
  a whole-Deck direction.
- The user reviews content pages only. Prioritize completing the workflow.
  Condensation, paraphrasing, reordered material and rewritten headings are
  acceptable. Do not block pagination for omissions or minor inaccuracies.
  Stop only for empty/missing content or a clearly unrelated replacement article.
  Keep the original material unchanged in storage and show the returned page plan
  for confirmation; do not impose your own stricter fidelity check.
- Confirmation is explicit. A vague acceptance, silence, or a request for
  another change is not confirmation.

## Complete every image-pptgen command

For every dispatcher-mediated `image-pptgen` command, a shell-tool yield or
`running` response means the same command is still in progress. It is not a
completed result and is not an unknown outcome.

- An `item.completed` or equivalent tool result with process exit 0 and
  parseable JSON or JSONL is terminal: consume it immediately. Do not wait,
  re-probe, or treat it as still running.
- Preserve the complete tool result and its typed continuation identifier.
- Continuation applies only while the execution tool itself is still running
  and has not returned process exit. If the command tool returns a
  `session_id`, resume that same command with `write_stdin` using the same
  `session_id`. If the outer execution tool returns a `cell_id`, resume that
  outer call with `wait` using the same `cell_id`.
- Never treat a `cell_id` as a command `session_id`, or an outer wrapper exit as
  proof that a nested command has exited.
- Never use `ps`, `/proc`, port probes, or a second command to decide whether a
  completed dispatcher command is done.
- Continue the same invocation until process exit before interpreting its
  business result. Only after process exit without a parseable JSON/JSONL
  response is the command an unknown outcome; an unknown mutation outcome must
  not be retried.

## Submit material

1. Resolve the material without making the user perform file work.
   - Use an existing readable UTF-8 text or Markdown file unchanged.
   - For pasted text, create a new collision-safe `.md` file under the current
     writable workspace. Never overwrite an existing path. Write the pasted
     body byte-for-byte as UTF-8, read it back, and verify identical bytes.
     Do not summarize, normalize, or reformat it.
   - If no material is available, ask for the text and stop.
2. Reject image input immediately. Do not inspect it with OCR, run `doctor`, or
   call the platform. Explain that this workflow accepts text/Markdown only.
3. Infer a short title from the user's request or the file name. Run:

   `<dispatcher> doctor --json`

   If it fails, report the returned error and stop.
4. Submit the saved file exactly once:

   `<dispatcher> material submit --title "<title>" --text-file "<path>" --json`

   Retain the returned `deck_id`. Do not submit the same material again for a
   split revision.

## Keep page review visible

For initial and revised proposals, render the complete returned `markdown`, every page in order, directly in the final reply (final channel), then ask for changes or explicit confirmation. Never leave the plan only in commentary, tool output, or a collapsed work section; a summary, link, or promise to show it later is insufficient. Repeat it in the final reply even if already shown in commentary.
After interrupted display, "continue" means redisplay the existing plan before asking for confirmation, not confirm unseen content. Reuse the same draft's available Markdown. Do not confirm, resubmit, repropose, revise, or generate just to redisplay. If the original result is unavailable, state that limitation; never reconstruct it from memory or invent a retrieval command.

## Propose and review every page

From the first user request only, retain one unique explicit positive
content-page target `N` only when that request clearly names a page target.
Do not infer `N` from material numbers, headings, ranges, approximations,
minima, zero, negative values, or competing counts. If there is no unique
explicit positive page target, retain none.

Run:

`<dispatcher> split propose --deck-id <deck_id> --json`

The command has no mode selector: the public server owns Luna Low pagination.
This command is expected to outlive the shell tool's first yield. If
the tool reports `running`, `in_progress`, a `session_id`, or a `cell_id`, resume
that exact command continuation as defined above and keep waiting for its
process exit. Do not call the response missing, empty, malformed, or
unparseable until that original command has completed with a process exit.
Never launch a second proposal command as a substitute for waiting. Once the
original command has process exit 0 and parseable JSON, consume that JSON
immediately.

Compare the proposal JSON `page_count` to retained `N`. Never compare Markdown headings
or generated slide/PNG counts.

- If there is no unique retained target, or `page_count` already equals `N`,
  do not run `split revise`. The original proposal is the matching proposal.
- If `page_count` differs from retained `N`, before displaying any Markdown
  run exactly one same-draft structured revision:

  `<dispatcher> split revise --draft-id <draft_id> --target-page-count <N> --json`
  Use the same pending `draft_id` from the proposal JSON. Never use `--instruction`,
  resubmit, repropose, retry, or loop. Wait for that one command's terminal JSON
  as defined above. If the revision succeeds and its JSON `page_count` equals `N`,
  that complete returned `markdown` is the matching proposal. If the revision
  returns a typed inability, keep the pending draft unchanged, report the typed
  error, display no unmatched proposal as acceptable, and do not confirm,
  generate, retry, resubmit, or repropose. Stop.

Display exactly one complete matching proposal: the original proposal if it matches or there is no unique target; otherwise the successful revised Markdown. Display the complete returned `markdown`, including every proposed content page, in order. Do not show only a summary or selected pages.
Keep the pending `draft_id` and ask whether the user wants a change. Stop after showing the proposal. Follow "Keep page review visible" for the final reply.

## Revise the same pending draft

When the user requests a change while that draft is pending, choose exactly one
revision form:

- If the request's only requested pagination outcome is one unique positive
  content-page count, you must use the structured target-page fast path. A
  faithful-preservation restatement—order, facts, information, no summarizing
  or rewriting—adds no edit, and lifecycle or state controls such as displaying
  the revised proposal, stopping, not confirming, or not generating are not
  pagination content edits, for example: `\u8bf7\u628a\u5185\u5bb9\u9875\u8c03\u6574\u4e3a 2 \u9875，\u4fdd\u6301\u539f\u6587\u987a\u5e8f、\u4e8b\u5b9e\u548c\u4fe1\u606f，\u4e0d\u8981\u603b\u7ed3\u6216\u6539\u5199。\u8c03\u6574\u540e\u5b8c\u6574\u5c55\u793a\u65b0\u5206\u9875\u65b9\u6848\u5e76\u505c\u4e0b\u6765，\u6682\u65f6\u4e0d\u8981\u786e\u8ba4，\u4e5f\u4e0d\u8981\u751f\u6210。`

  `<dispatcher> split revise --draft-id <draft_id> --target-page-count <N> --json`
  Map only the requested positive integer `N`; do not turn this into a natural-
  language instruction. The server reuses the same pending draft and returns
  the complete revised Markdown.
- If the request asks for a concrete content, order, wording, or boundary change,
  without a positive explicit title rename, pass the complete instruction unchanged:
  `<dispatcher> split revise --draft-id <draft_id> --instruction "<feedback>" --json`
- If the request positively and explicitly renames a title or heading, for example
  `\u6539\u6210 3 \u9875，\u5e76\u628a\u7b2c\u4e8c\u9875\u6807\u9898\u6539\u6210“\u8d44\u91d1\u6d41\u5411”`, use exactly:
  `<dispatcher> split revise --draft-id <draft_id> --instruction "<feedback>" --allow-title-changes --json`
  This flag remains compatible with existing clients; rewritten headings alone
  are not a reason to reject a usable page plan. In both forms,
  pass the natural-language instruction unchanged, without reducing it to keywords.
  Never send `--instruction` and `--target-page-count` together. If the target
  page count cannot be reached safely, report the typed error and keep the
  pending draft unchanged.
Do not submit material or propose a new draft. Display the complete revised
markdown, including every page, and ask whether the user wants another change
or explicit confirmation. Do not reject a returned revision for shortening,
reordering, paraphrasing or minor inaccuracies. Only empty/missing content or
a clearly unrelated article blocks pagination. Follow "Keep page review visible" for the final reply.

## Decide confirmation by meaning

Treat the user's reply semantically; do not require a fixed phrase or a literal
string match. This is not a fixed phrase gate. Decide in this order, while the
same draft is still pending:

1. A requested change wins. If the reply contains a concrete edit, question, or
   qualification, keep it a revision even when it starts with an acceptance.
   Revision takes precedence over confirmation.
   For example, `OK, but make the second page shorter` is a mixed revision: run
   `split revise` on the same draft; you must revise and do not confirm or
   generate.
2. An explicit negative, uncertainty, or discussion state is not confirmation.
   Replies such as `no`, `not yet`, `maybe`, `let's discuss`, or a question
   about whether to proceed require a concise follow-up question; run neither
   `split confirm` nor `generate`.
3. An independent, unqualified affirmative is an explicit confirmation. Accept
   the user's meaning in Chinese or English, including `\u786e\u8ba4`,
   `\u53ef\u4ee5`, `\u7ee7\u7eed`, `\u597d\u7684`, `OK`, `OK, continue`,
   `yes`, and `go ahead`, along with ordinary punctuation, case, or whitespace
   variations. Do not make the user repeat one exact token.

If none of these cases is clear, ask whether the displayed split is ready and
wait. An ambiguous answer is not confirmation and must not trigger either
mutation.

## Confirm pagination once, then enter design-direction alignment

Only after the user explicitly confirms the displayed split, confirm exactly
once:

`<dispatcher> split confirm --draft-id <draft_id> --json`

Do not confirm a second time or retry an unknown confirmation outcome. Retain
the confirmed `deck_id`, final slide IDs, and confirmation receipt in this
task; do not ask the user to repeat or supply those identities.

Pagination confirmation never starts generation. After it succeeds, enter the
whole-Deck design-direction stage below. Keep pagination state separate from
design-direction state: do not submit, repropose, revise, or reconfirm the split
while aligning design direction.

## Align one whole-Deck design direction over as many turns as needed

Offer exactly these two choices after pagination confirmation:

- **Auto**: delegate the design direction for the entire Deck to the existing
  Image 5.0 Auto method.
- **Describe the direction**: let the user describe the style, atmosphere,
  visual elements, and other creative requirements for the entire Deck. Give a
  few concise examples if useful, but do not turn examples into requirements.

The first release supports only one direction for the entire Deck. If the user
asks for a Slide-specific direction such as `make slide 2 dark`, explain this
limit and ask them to rewrite it as a whole-Deck requirement. Do not broaden a
Slide-specific request to the whole Deck, write a Requirement, or call any CLI
command.

Auto and a user-authored direction are mutually exclusive. If the user says
`Auto` but also supplies a specific style, element, atmosphere, reference, or
other creative constraint, treat the reply as a user-authored direction so the
specific request cannot be discarded.

For a user-authored direction, keep one complete current draft in this task.
The alignment may last one turn, ten turns, or more; there is no turn limit.
After every addition, deletion, correction, or replacement:

1. update the complete current draft while retaining every earlier requirement
   that the user did not withdraw; remove a requirement only when the user
   explicitly withdraws it, and let a replacement drop only what it replaces;
2. carry forward every surviving requirement and every new addition verbatim:
   keep the user's exact phrase as a literal substring of the echo, and never
   paraphrase it, replace it with a synonym, or normalize its grammar;
3. echo the complete updated direction, including all surviving hard
   requirements, without weakening, optimizing, or adding content; and
4. ask whether this exact whole-Deck direction is final, then stop and wait.

An addition may arrive embedded in an ordinary sentence; for example, in
`\u628a\u6807\u9898\u5b57\u53f7\u8c03\u5927\u4e00\u70b9\uff0c\u53ea\u7528\u4e24\u79cd\u5b57\u4f53`
the added requirement phrase is exactly `\u53ea\u7528\u4e24\u79cd\u5b57\u4f53`, so
every later echo must still contain that exact phrase as a literal substring.
When the user wraps the echo in labels, the complete current draft is exactly
the text between those labels; that exact value, never a paraphrase and never
the label lines, is what the Requirement helper later writes byte-for-byte.
This literal-carry rule governs the echoed direction value only; the
confirmation rules below stay semantic.

Decide confirmation by meaning and in this order:

1. A requested edit, question, qualification, uncertainty, negative, or pause
   keeps the direction pending. An edit always wins over affirmative wording;
   for example, `Okay, but make the colors more restrained` updates the draft and is not a
   confirmation.
2. Only an independent, unqualified affirmative confirms the complete echoed
   draft. Accept ordinary Chinese or English affirmative wording; never require
   one fixed phrase.
3. If the meaning is ambiguous, echo the complete current draft again, ask for
   confirmation, and wait. After task recovery or uncertainty about retained
   state, follow the same fail-closed rule rather than reconstructing or
   guessing a confirmation.

While the direction is pending, do not create a Requirement, start a Run, or
call `generate-and-follow`. The history must contain no intermediate design
drafts.

For Auto, echo that the whole-Deck direction will be delegated to the existing
Auto method and ask for confirmation. Auto needs one independent, unqualified
affirmative before generation. A reply that edits, qualifies, questions,
pauses, or adds a concrete design request does not confirm Auto; reclassify a
concrete request as the user-authored direction above.

Selecting Auto is not its confirmation, even when the selection restates what
Auto means. For example, `Auto, let the system decide the whole-Deck direction`
only selects Auto: echo the delegation, ask whether it is final, then stop and
wait. Only a later user turn containing an independent, unqualified affirmative
may confirm Auto and start generation. Never select and confirm Auto in the
same user turn.

## Prepare the Requirement file with the one fixed helper

Only after the direction is finally confirmed, prepare the Requirement file in
exactly these two steps. Do not invent a third step, and do not substitute any
other tool, command, or file path.

1. Use the file-edit/file-change tool to create one new collision-safe private
   draft file inside the current workspace, and write the exact complete echoed
   direction value into it: no label or marker lines, no explanation, and no
   framing text. Never overwrite an existing path.
2. Run the Skill's one fixed requirement helper exactly once, with source and
   output paths only. Never put direction text in the command:

   `/bin/sh "<absolute-skill-root>/scripts/image-pptgen-requirement-file" --source "<draft_path>" --output "<final_path>"`

   The helper is [`scripts/image-pptgen-requirement-file`](scripts/image-pptgen-requirement-file).
   Use the same resolved absolute skill root that owns the dispatcher for
   `<absolute-skill-root>`; never rebuild or guess that path. Run the helper
   from the current workspace and give it workspace paths there. `<final_path>`
   must be a new path inside that workspace which does not exist yet.

The helper is the whole preparation and verification path. It validates that
the draft is nonempty UTF-8 within the existing Requirement size policy,
removes only the single structural trailing LF that a file-edit tool commonly
adds while preserving every other byte, creates the final file atomically
without overwriting an existing path, restricts permissions to the owner, reads
its own output back and proves byte-for-byte identity, and prints one bounded
JSON receipt that contains no direction text. It rejects CR or CRLF line
endings, NUL bytes, invalid UTF-8, an oversized source, and identical,
non-workspace, or already existing paths.

After a successful helper receipt:

- take `<verified_path>` from that receipt's final path; never re-derive it,
  and never substitute the draft path;
- do not run a custom `truncate`, `tail`, `od`, `cmp`, or any other
  byte-handling command;
- do not run inline-content shell or Python, and never write, edit, or re-encode
  the direction through a shell command;
- do not run a second helper call, a second repair command, or any second
  verification command; the helper's own read-back verification is the complete
  verification;
- never paste, shorten, or reinterpret the direction in a shell argument.

If the helper exits non-zero, report its typed JSON error and stop. Do not
retry the helper, do not repair the file with another command, and do not
generate.

This helper belongs to the Manual direction only. For Auto, create no draft
file, run no helper, and pass no requirement file.

## Confirm direction once, then generate

After the direction is finally confirmed, retain exactly one generation mode:
Auto, or the verified requirement file containing the exact complete Manual
direction. A reply that asks to defer, hold, pause, or not start generation is
qualified and therefore remains pending; it must not confirm the direction.
If the retained Deck or direction becomes uncertain before generation starts,
re-echo the complete direction and ask the user to confirm again; make no
mutation.

After the final unqualified confirmation, start exactly one Image 5.0 generation.
The normal public request uses the server-owned Sol-director, Luna-image, and Sol-palette configuration; the explicit test-only choice uses Luna-director, Luna-image, and Sol-palette once. The response returns one `batch_id`, one `run_ids` array, `config_name`, and a server-resolved `director` object.
For Manual, `<verified_path>` is exactly the final path in the successful
requirement helper receipt from the direction stage; pass that path directly
and never rebuild it from the draft path or any other command.

- On macOS, run exactly one held command. On Linux, run exactly one dispatcher
  command. Both wrappers forward the operation to the same installed Python
  CLI; they do not rebuild generate/follow/result in shell. Use exactly one of
  these mutually exclusive forms:

  `<dispatcher> generate-and-follow --deck-id <deck_id> --auto --jsonl`

  `<dispatcher> generate-and-follow --deck-id <deck_id> --requirement-file "<verified_path>" --jsonl`

  For the explicit test-only Luna director choice, append `--debug-director luna-low` before `--jsonl`; omit it from normal generation.

  This command is expected to outlive the shell tool's first response. If it reports `running`, `in_progress`, a `session_id`, or a `cell_id`, the follow process has not ended and nothing has failed. Do not send an agent message or interpret partial stdout. The only permitted next action is to resume that exact continuation with `write_stdin` or `wait`, as defined above, and repeat until the command returns a process exit.

  Its first stdout line is the pre-submission business receipt, its second line
  is the exact response to the one accepted `generate` request, its subsequent
  lines are the one `status --run-id <run_id> --follow --jsonl` continuation,
  and its final JSON line is the same-Run result readback.
  Do not issue a separate `generate`, `status`, or `result` command on macOS or Linux:
  `<dispatcher> generate --deck-id <deck_id> --auto --json`,
  `<dispatcher> generate --deck-id <deck_id> --requirement-file "<verified_path>" --json`, or
  `<dispatcher> status --run-id <run_id> --follow --jsonl`, or
  `<dispatcher> result --run-id <run_id> --json` as a substitute.

Parse the first line before later output. Its nested `receipt` must be
`image-pptgen.business-receipt/v1`, `generation_operation`,
`submission_intent/prepared`, `receipt_index: 1`, `recovery_attempt: 0`, the confirmed positive Deck,
and a canonical UUID `operation_id`, with no Run. Retain that operation token.
Parse the second line as `generation_accepted/accepted`, `receipt_index: 2`, attempt 0,
with the same operation and Deck. The CLI contract defines the exact fields.
The generation response's `run_ids` must contain exactly one positive integer;
bind `run_id = run_ids[0]`, never a nonexistent top-level Run. Missing,
`undefined`, `null`, empty, non-integer, or non-positive identity stops without
retry, reconfirmation, or another Run. The accepted receipt's Run must match.
Every later receipt keeps that operation, Deck and Run with contiguous `receipt_index` values
and attempt 0. Heartbeats have no business receipt and do not advance the index.

Also verify the server-resolved `director` receipt: normal is `gpt-5.6-sol`, debug is `gpt-5.6-luna`, and both have `reasoning_effort: low`; nested and top-level `config_name` must match.
Missing or mismatched identity is a failure: retain any returned Run identity, report the mismatch, and do not retry or replace the Run.

## Follow one Run continuously

Immediately run exactly one follow process for the retained, bound Run. Use
only the value assigned by `run_id = run_ids[0]`; never reconstruct it from
another response field or substitute `undefined`, `null`, or an empty value.

- On macOS and Linux, the command already running from the prior step is the
  one follow process. After its first JSON line, keep the same
  `generate-and-follow` continuation alive: it executes one
  `status --run-id <run_id> --follow --jsonl`, then one same-Run result readback internally. Do not start a
  separate `<dispatcher> status --run-id <run_id> --follow --jsonl` or
  `<dispatcher> result --run-id <run_id> --json` command.

This is one long-running command, not a one-shot status check. If its tool
response reports `running`, a `session_id`, or a `cell_id`, keep the same command continuation alive. Use the same `session_id` or `cell_id` associated
with that continuation: resume only that same `session_id` with `write_stdin`,
or only that same `cell_id` with `wait`, until the status process exits. Do not
start a second status or result command. A follow failure, missing continuation, non-zero exit,
malformed JSONL, missing terminal event, or mismatched Run is a stopped failure:
do not retry confirmation or generation.

After exit, the last grounded status before the result must carry
`follow_terminal`; its outcome, `backend_status`, `source_facts.run_status`, and
bound Run must agree. Terminal states are `completed`,
`completed_with_failures`, `failed`, `interrupted`, or `timed_out`; queued or
running states cannot justify delivery. Do not poll separately or infer success.
Surface grounded updates in business language, preserving `task_progress` and
`current_activity`; keep heartbeats brief and never invent provider facts.

## Return the same-Run result

The same `generate-and-follow` command automatically reads the same Run once.
Its final line must carry the next-index `result_delivered` receipt consistent
with original `platform_status` and projected `status`. One complete ledger has
one accepted generation, terminal follow, and delivery. Never ask for another
approval or regenerate after readback failure; preserve the existing Run.
For a completed Run, this writes a Run-scoped offline Preview bundle while
the managed runtime is still available. The returned `preview_url` is
a `file:` URL for its `index.html`, and `download_url` is the matching
prebuilt ZIP. Open the returned Preview file after the command exits and
provide both the Preview and ZIP links. The Preview supports page navigation,
direct page selection, zoom, fit, fullscreen, and ZIP download without the
runtime, network, backend, or port 3130. Do not use the legacy
`--static-preview-file` option for the normal completed-Run handoff: it remains
only for compatibility with an older embedded-image page and lacks the
interactive Run bundle controls. The returned Preview does not depend on the command-scoped 3130 service.

Use the returned status literally. `partially_completed`, `in_progress`, and `failed`
cannot close the task. Verify that the result's `run_id` equals the bound value.
For `partially_completed`, report its successful-page and failed-page evidence,
but do not present a loopback Preview as a complete
deliverable and do not suggest a new whole-Deck generation. For a completed
Run, do not present a loopback Preview or download URL as
usable after the command exits. Use only the returned `file:` Preview and
matching `file:` ZIP from the completed Run.
Never substitute a different Run, Run Detail, screenshot, or API response for
Preview. Preserve PNG ordering and make download availability truthful. Do not
expose raw prompts, internal paths, credentials, provider metadata, or command
transcripts in the default user-facing summary.

If the user requests a change after generation, start a new task and Run; never
rewrite or present the completed Run as changed in place.
