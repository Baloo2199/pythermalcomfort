---
name: copilot-review
description: Request, wait for, and act on a GitHub Copilot code review on a pythermalcomfort PR. Use whenever a PR is opened or pushed to and its automated review needs requesting, checking, or re-triggering — including before merging any PR.
---

# GitHub Copilot code review

Copilot code review is a separate, cloud-only reviewer from CodeRabbit (see the
`coderabbit` CLI usage in the global `CLAUDE.md`, and the release skill's step 5
for running it locally). It cannot run locally or offline — every review is a
request against GitHub's infrastructure.

## It is already auto-requested, once, per PR

Both `development` and `master` have a branch ruleset with a `copilot_code_review`
rule (`review_on_push: false`, `review_draft_pull_requests: false`). That means:

- Opening a PR against either branch **automatically requests one Copilot
  review** — you do not need to request the first one yourself.
- Pushing new commits does **not** trigger a fresh review, and the branch's
  `pull_request` rule has `dismiss_stale_reviews_on_push: true`, which dismisses
  any prior approval. The result: after any push to an open PR, the most recent
  Copilot review on file is stale (posted against an earlier commit) until you
  explicitly request a new one. Check the review's commit before trusting it:

  ```bash
  gh api repos/pythermalcomfort/pythermalcomfort/pulls/<n>/reviews \
    --jq '.[] | select(.user.login=="copilot-pull-request-reviewer[bot]") | {commit: .commit_id, state}'
  gh pr view <n> --json headRefOid -q .headRefOid   # compare against this
  ```

  If they don't match, re-request:

  ```bash
  gh pr edit <n> --add-reviewer @copilot
  ```

  (`gh pr create --reviewer @copilot ...` does the same at PR-creation time, but
  is redundant here since the ruleset already requests one on open.)

## Waiting for it

A review usually lands within 1-2 minutes. Poll rather than merge immediately
after opening or updating a PR:

```bash
gh api repos/pythermalcomfort/pythermalcomfort/pulls/<n>/reviews \
  --jq '.[] | select(.user.login=="copilot-pull-request-reviewer[bot]")'
```

An empty result means it hasn't posted yet — wait and retry (use `Monitor` with a
poll loop rather than blocking `sleep`, since this can take a couple of minutes).

## Reading and acting on it

The review's top-level `body` carries a verdict ("🟢 Approval recommended" /
otherwise) plus a file-by-file summary. Line-level findings, if any, come back
as separate PR review comments:

```bash
gh api repos/pythermalcomfort/pythermalcomfort/pulls/<n>/comments \
  --jq '.[] | select(.user.login=="copilot-pull-request-reviewer[bot]") | {path, line, body}'
```

Treat a real finding the same as a human reviewer's: fix it, or explain in the PR
why not. Do not merge a PR whose current-commit Copilot review is still pending,
and do not treat a review posted against an older commit as covering the current
one.

## Effort level (Lite vs Balanced)

Copilot reviews at one of two effort levels — **Lite** (targeted, cheaper) or
**Balanced** (deeper analysis, more AI credits). As of writing this is **not**
exposed through any API or config file the repo can check in — no
`gh` flag, no REST/GraphQL parameter, no per-repo YAML. It is set only through
the GitHub web UI:

- **Per-request**: the "Reviewers" bar on a PR lets you pick the effort level
  before requesting a review manually.
- **Repo default**: Settings → Copilot → Code review.
- **Org default**: org Settings → Copilot → Code review (falls through to
  repos that haven't set their own).

Since the ruleset auto-requests the review (not a manual click), it always runs
at whatever default is currently configured for this repo/org — check there if
you need a different level, this skill cannot set it for you. Note GitHub's
platform-wide default changes from Lite to Balanced on 2026-09-28.

## Custom instructions Copilot reads

Copilot's automated review reads (in this order of specificity), from the PR's
**head branch**, not the base branch:

- `.github/copilot-instructions.md` (already present in this repo)
- `.github/instructions/**/*.instructions.md` (path-specific)
- A `.github/skills/<name>/SKILL.md`-style agent skill, if one exists — this is
  a different namespace from our own `.claude/skills/`, and not currently used
  in this repo (Copilot's own review comments link to
  `.github/skills/code-review/SKILL.md` as a suggestion to add one).

If Copilot's reviews are missing context it should have, that file is the lever
— not this skill, and not `.claude/CLAUDE.md` (which Copilot does not read).
