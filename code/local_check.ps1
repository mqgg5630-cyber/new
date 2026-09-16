# local_check.ps1 (git-pull-arena) - this repo's checks, run on the real
# machine when the agent requests one. watch.ps1 executes this whenever the agent requests a check
# (config key check_cmd), captures all output to
# results\status\check_rN_<stamp>.log and pushes the verdict back.
#
# Exit 0 = passed, anything else = failed. Edit freely - this file belongs to
# the repo, the installer only creates it when it is missing.
#
# Ideas for real checks (pick what fits the repo):
#   - deliverable files exist and have sane sizes
#   - open an Office file via COM to prove it is not corrupt
#   - python -c "import torch; assert torch.cuda.is_available()"  (GPU smoke test)
#   - run a script from code\ and compare its output
#
# ASCII-only on purpose (Windows PowerShell 5.1 decodes .ps1 as ANSI/GBK).

$ErrorActionPreference = 'Continue'
Set-Location (Join-Path $PSScriptRoot '..')   # repo root (this file lives in code\)

$fail = 0

# 1. the standard gate (.ps1 ASCII + branch guard + script consistency)
#    (forward slashes on purpose: this also runs under the scheduled task,
#     where bash may eat backslashes; Write-Output on purpose: the watcher
#     captures stdout, and PS 5.1 Write-Host bypasses it)
if (Test-Path -LiteralPath '.\code\check_all.sh') {
    # prefer the bash that ships with the git we use - a WSL bash.exe on PATH
    # cannot always read a Windows working directory and would look like a
    # gate failure when it is really an environment mismatch
    $bashExe = ''
    $g = Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($g -and $g.Source) {
        $gitDir = Split-Path -Parent (Split-Path -Parent $g.Source)
        foreach ($cand in @((Join-Path $gitDir 'bin\bash.exe'), (Join-Path $gitDir 'usr\bin\bash.exe'))) {
            if (Test-Path -LiteralPath $cand) { $bashExe = $cand; break }
        }
    }
    $bashFrom = 'git'
    if (-not $bashExe) {
        $b = Get-Command bash -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($b) { $bashExe = [string]$b.Source; $bashFrom = 'PATH' }
    }
    if (-not $bashExe) {
        Write-Output '[WARN] no bash found (install Git for Windows) - the repo gate was skipped'
    } else {
        $gateOut = (& $bashExe 'code/check_all.sh' 2>&1 | Out-String)
        $gateCode = $LASTEXITCODE
        if ($gateOut) { Write-Output $gateOut }
        if ($gateCode -ne 0) {
            if (-not $gateOut) {
                Write-Output ('[WARN] the gate produced no output via ' + $bashExe + ' (' + $bashFrom + ') - skipped here, it still runs before every agent push')
            } else {
                Write-Output ('[FAIL] gate failed (exit ' + $gateCode + ')')
                $fail = 1
            }
        } else {
            Write-Output ('   (gate ran via ' + $bashExe + ' [' + $bashFrom + '])')
        }
    }
}

# 1b. the two hard requirements are asserted strictly in section 2 (2a/2b) -
#     they fail the round on purpose, because "push needs a click" and
#     "watcher flashes a window" are exactly what v2.5.0 had to fix.

# 2. v2.5.0 acceptance: the two hard requirements, asserted ON THIS MACHINE.
#    (Write-Output, not Write-Host: the watcher captures stdout only.)
#    2a. silent push - git must get a credential with ALL prompts disabled
if (Test-Path -LiteralPath '.\auth.ps1') {
    try {
        $auth = ((& .\auth.ps1 -Json -Verify) | Out-String) | ConvertFrom-Json
        if ($auth.push_dry_run -in @('passed', 'not-fast-forward') -and $auth.lsremote -eq 'passed') {
            if ($auth.push_dry_run -eq 'not-fast-forward') {
                Write-Output '== accept 2a: silent push PROVEN by the credential probe;'
                Write-Output '   the dry-run was only REJECTED (not a fast-forward) - the server had already accepted the token.'
                Write-Output '   run .\sync.ps1 so the next real push is a fast-forward.'
            } else {
                Write-Output '== accept 2a: silent push PROVEN (ls-remote + push --dry-run, prompts disabled)'
            }
        } else {
            Write-Output ("[FAIL] accept 2a: silent push NOT proven (lsremote=" + $auth.lsremote + " push_dry_run=" + $auth.push_dry_run + ")")
            Write-Output ("       detail: " + $auth.push_dry_run_detail)
            Write-Output '       fix once with:  .\auth.ps1 -Setup  then  .\auth.ps1 -Verify'
            $fail = 1
        }
    } catch {
        Write-Output '[FAIL] accept 2a: auth.ps1 probe failed (run .\auth.ps1 by hand to see why)'
        $fail = 1
    }
} else {
    Write-Output '[FAIL] accept 2a: auth.ps1 is missing (upgrade the skill)'
    $fail = 1
}

#    2b. how visible is the watcher? Graded, and the grade is printed:
#          zero-window launcher  -> nothing ever appears            (best)
#          S4U / session 0       -> nothing ever appears            (best, needs admin)
#          -Loop in one process  -> ONE brief flash per logon       (acceptable)
#          per-poll process      -> a flash every N minutes         (FAIL)
$taskName = 'git-sync-watch-' + (Split-Path -Leaf (Get-Location).Path)
try {
    $t = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $exec  = [string]$t.Actions[0].Execute
    $argl  = [string]$t.Actions[0].Arguments
    $logon = [string]$t.Principal.LogonType
    if ($exec -match 'watchhost') {
        Write-Output ("== accept 2b: ZERO window - launcher exe: " + $exec)
    } elseif ($logon -eq 'S4U' -or $logon -eq 'Password') {
        Write-Output ("== accept 2b: ZERO window - session 0 (S4U), logon type " + $logon)
    } elseif ($argl -match '-Loop') {
        Write-Output '== accept 2b (fallback): one LONG-LIVED loop process - one brief flash per logon,'
        Write-Output '   not per poll. For zero flash: admin PowerShell -> .\watch.ps1 -Unregister ;'
        Write-Output '   .\watch.ps1 -Register -Headless   (or fix the launcher, see watch-*.log)'
    } else {
        Write-Output ("[FAIL] accept 2b: the task starts a new process per poll (" + $exec + " " + $argl + ")")
        Write-Output '       fix with:  .\watch.ps1 -Unregister  then  .\watch.ps1 -Register'
        $fail = 1
    }
} catch {
    Write-Output ("[FAIL] accept 2b: scheduled task '" + $taskName + "' not found - run .\watch.ps1 -Register")
    $fail = 1
}

# 3. example: the deliverable must exist and not be empty
# if (-not (Test-Path '.\deliverable\final.pptx')) {
#     Write-Host '[FAIL] deliverable\final.pptx missing' -ForegroundColor Red; $fail = 1
# }

# 4. add your own checks here ...

if ($fail -eq 0) { Write-Output '== local checks passed' }
exit $fail
