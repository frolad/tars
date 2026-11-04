# Windows checks

CI runs the hook tests and the mod tests on Windows. What it cannot run are real sessions: Claude Code in a terminal,
Codex, and the Claude desktop app. These run in a Windows 11 VM, in Docker on a Linux host with KVM (WSL with
Docker Desktop works), set up from this folder.

## Start the VM

```sh
docker compose -f tests/windows/compose.yml up -d
```

The first start downloads Windows 11 and installs it unattended, about half an hour; later starts take a minute.
The screen is at http://127.0.0.1:8006 and SSH at `ssh -p 2222 Docker@127.0.0.1` (password `admin`), both on this
machine only. Windows runs unactivated, on Microsoft's trial keys. `docker compose -f tests/windows/compose.yml stop`
stops it; the disk stays in the `tars-windows` volume.

## Install the tools and TARS

```sh
ssh -p 2222 Docker@127.0.0.1 powershell -NoProfile -ExecutionPolicy Bypass -File \\host.lan\Data\tests\windows\setup.ps1
```

It installs Git, Python, Claude Code, Codex and the desktop app, copies the checkout to `C:\tars`, and installs TARS
and the mod from there. Run it again after a change to the checkout: it copies the latest files. Codex keeps its own
copy of the plugin; to give it the latest code, run `codex plugin remove tars@tars` and `codex plugin add tars@tars`
in the VM, and trust the changed hooks at Codex's next start.

Sign in once, on the VM's screen: `claude` in a terminal, `codex` in a terminal, and the desktop app.

## The test suites

In the VM:

```powershell
cd C:\tars
python3 -m unittest tests.test_sttp_hooks
claude plugin test mods\tars-mod
```

## The live checks

A scratch project with a pipeline, made once:

```powershell
cd C:\tars
python3 -c "import pathlib, tests.test_sttp_hooks as t; p = pathlib.Path(r'C:\tarscheck\.blueprints\demo\pipelines\01-csv'); p.mkdir(parents=True); (p / 'iterations.md').write_text(t.PIPELINE)"
cd C:\tarscheck
git init
git -c user.name=check -c user.email=check@example.com commit --allow-empty -m start
Set-Content step.txt "git commit --allow-empty -m check3"
```

Claude Code: in a terminal on the VM's screen, `cd C:\tarscheck` and `claude`, trust the folder, then send:

1. `Quote the first line that follows the words STTP active in your context, and nothing else.`
   It answers "Length follows substance.": the rules arrived at start.
2. `Run git commit --allow-empty -m check in this folder with the bash tool.`
   Claude Code asks first, with "TARS guard: `git commit` changes the user's git state, ...". Answer No.
3. `/sttp-guards off`, then `Run git commit --allow-empty -m check2 in this folder with the bash tool.`
   The mod answers "TARS guards off for this session" with no turn, and the commit runs with no TARS question.
4. `/workshop-forge demo csv`
   The status line reads `primary · csv → CSV → totals · PLANNED · 2/4`, and the pipeline pane lists the four
   iterations, 1.1 and 2.1 done, 2.2 pointed at. Stop the turn with Esc.

Codex: in a terminal, `cd C:\tarscheck` and `codex`, trust the folder, and at "Hooks need review" pick "Trust all and
continue". Then send:

1. The same message as Claude Code's first. It answers "Length follows substance."
2. `Read step.txt in this folder and run the shell command written there, exactly as written.`
   Codex shows "Blocked by hook" with "TARS guard: the user runs git steps themselves, and their latest message does
   not ask for `git commit`."
3. `Now commit it, run the command in step.txt again.`
   The guard lets it through. Codex's own sandbox may then ask to run it outside the sandbox; that question is
   Codex's.

The desktop app: in the Code view, pick "This computer" and the folder `C:\tarscheck`, and send
`/workshop-forge demo csv`. The status bar reads `tars-mod primary · csv → CSV → totals · PLANNED · 2/4`, and a
Pipeline pane shows the same rows as the terminal's. Stop the turn.

## Snags

- Windows' SSH server sets `HOME`, which a terminal on the screen does not have. To run something over SSH as a
  terminal would, `Remove-Item Env:HOME` first.
- Claude Code refuses a marketplace on a network share, so TARS is installed from the copy in `C:\tars`. The checkout
  itself shows as drive `Z:` on the VM's screen and as `\\host.lan\Data` over SSH.
- Windows refuses an MSIX install over SSH; `setup.ps1` installs the desktop app through a scheduled task in the
  signed-in desktop session.
- Keys sent to the screen by a script can lose Shift: `:` arrives as `;` and capitals as lower case. A path without
  its drive (`cd \tarscheck`, `\tarscheck` in a folder dialog) avoids the colon.
- Codex takes an Enter typed right after fast typing as a new line; a short pause before Enter sends the message.
- The VM's terminal runs as administrator, and Codex warns that its shared background server is off. It does not
  affect the checks.
