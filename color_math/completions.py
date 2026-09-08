"""Shell autocompletion script generators for color-math."""

from __future__ import annotations

SHELLS = ["bash", "zsh", "fish", "powershell"]

THEME_CHOICES = "default catppuccin nord light"
PRESET_CHOICES = "all minimal extended"
FORMAT_CHOICES = "auto markdown jupyter anki tex"
SHELL_CHOICES = "bash zsh fish powershell"

ALL_FLAGS = [
    "-h", "--help",
    "-i", "--in-place",
    "-w", "--write",
    "-f", "--file",
    "-o", "--output",
    "-r", "--recursive",
    "--exclude",
    "--diff",
    "--check",
    "--dry-run",
    "--json",
    "--parse",
    "--format",
    "--theme",
    "-c", "--color",
    "--main-color",
    "--show-colors", "--show-palette",
    "--reset-colors", "--reset-palette",
    "--reset-config",
    "--init-config",
    "--config",
    "--preset",
    "--taxonomy", "--no-taxonomy",
    "--rainbow-delimiters", "--no-rainbow-delimiters",
    "--variable-data-flow", "--no-variable-data-flow",
    "--units", "--no-units",
    "--differentials", "--no-differentials",
    "--braket", "--no-braket",
    "--dimensionless", "--no-dimensionless",
    "--undo",
    "--ui", "--gui",
    "--tutorial",
    "-V", "--version",
    "-v", "--verbose",
    "-q", "--quiet",
    "--self-test",
    "--update-generated",
    "--generate-completion",
]


def generate_bash() -> str:
    opts = " ".join(ALL_FLAGS)
    return f"""# Bash completion for color-math / python-color-math
_color_math_completion() {{
    local cur prev
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    case "${{prev}}" in
        --theme)
            COMPREPLY=( $(compgen -W "{THEME_CHOICES}" -- "${{cur}}") )
            return 0
            ;;
        --preset)
            COMPREPLY=( $(compgen -W "{PRESET_CHOICES}" -- "${{cur}}") )
            return 0
            ;;
        --format)
            COMPREPLY=( $(compgen -W "{FORMAT_CHOICES}" -- "${{cur}}") )
            return 0
            ;;
        --generate-completion)
            COMPREPLY=( $(compgen -W "{SHELL_CHOICES}" -- "${{cur}}") )
            return 0
            ;;
        -o|--output|--config|--init-config)
            COMPREPLY=( $(compgen -f -- "${{cur}}") )
            return 0
            ;;
    esac

    if [[ "${{cur}}" == -* ]]; then
        COMPREPLY=( $(compgen -W "{opts}" -- "${{cur}}") )
        return 0
    fi

    COMPREPLY=( $(compgen -f -- "${{cur}}") )
}}

complete -F _color_math_completion color-math
complete -F _color_math_completion python-color-math
"""


def generate_zsh() -> str:
    return f"""#compdef color-math python-color-math
# Zsh completion for color-math / python-color-math

_color_math() {{
    local -a themes presets formats shells
    themes=({THEME_CHOICES})
    presets=({PRESET_CHOICES})
    formats=({FORMAT_CHOICES})
    shells=({SHELL_CHOICES})

    _arguments -s -S \\
        '(-h --help)'{{-h,--help}}'[Show help message]' \\
        '(-i --in-place -w --write)'{{-i,--in-place,-w,--write}}'[Write converted text back to file(s)]' \\
        '(-f --file)'{{-f,--file}}'[Treat target explicitly as file]' \\
        '(-o --output)'{{-o,--output}}'[Destination file]:file:_files' \\
        '(-r --recursive)'{{-r,--recursive}}'[Recursively scan directories]' \\
        '*--exclude[Glob pattern to exclude]:pattern:' \\
        '--diff[Display syntax-colored unified diff]' \\
        '--check[Linter/CI check mode]' \\
        '--dry-run[Report files that would change]' \\
        '--json[Output results in JSON format]' \\
        '--parse[Inspect nested function AST]' \\
        '--format[Input format]:format:($formats)' \\
        '--theme[Curated theme preset]:theme:($themes)' \\
        '*-c[Override color role]:color:' \\
        '*--color[Override color role]:color:' \\
        '--main-color[Override main function color]:hex:' \\
        '(--show-colors --show-palette)'{{--show-colors,--show-palette}}'[Print active palette]' \\
        '(--reset-colors --reset-palette)'{{--reset-colors,--reset-palette}}'[Restore factory defaults]' \\
        '--reset-config[Reset local .colormath.json]' \\
        '--init-config[Generate config template]:file:_files' \\
        '--config[Custom config file]:file:_files' \\
        '--preset[Feature preset]:preset:($presets)' \\
        '--taxonomy[Enable taxonomy]' \\
        '--no-taxonomy[Disable taxonomy]' \\
        '--rainbow-delimiters[Enable rainbow delimiters]' \\
        '--no-rainbow-delimiters[Disable rainbow delimiters]' \\
        '--variable-data-flow[Enable variable data-flow]' \\
        '--no-variable-data-flow[Disable variable data-flow]' \\
        '--units[Enable unit disambiguation]' \\
        '--no-units[Disable unit disambiguation]' \\
        '--differentials[Enable differentials]' \\
        '--no-differentials[Disable differentials]' \\
        '--braket[Enable bra-ket notation]' \\
        '--no-braket[Disable bra-ket notation]' \\
        '--dimensionless[Enable dimensionless groups]' \\
        '--no-dimensionless[Disable dimensionless groups]' \\
        '--undo[Strip color wrappers back to plain LaTeX]' \\
        '(--ui --gui)'{{--ui,--gui}}'[Open graphical window]' \\
        '--tutorial[Launch terminal tutorial]' \\
        '(-V --version)'{{-V,--version}}'[Show version]' \\
        '(-v --verbose)'{{-v,--verbose}}'[Verbose progress]' \\
        '(-q --quiet)'{{-q,--quiet}}'[Suppress output]' \\
        '--self-test[Run self-test suite]' \\
        '--generate-completion[Generate shell completion]:shell:($shells)' \\
        '*:file:_files'
}}

compdef _color_math color-math python-color-math
"""


def generate_fish() -> str:
    return f"""# Fish completion for color-math / python-color-math

for cmd in color-math python-color-math
    complete -c $cmd -s h -l help -d "Show help message"
    complete -c $cmd -s w -s i -l write -l in-place -d "Write converted text back to file(s)"
    complete -c $cmd -s f -l file -d "Treat target explicitly as file"
    complete -c $cmd -s o -l output -F -d "Destination file"
    complete -c $cmd -s r -l recursive -d "Recursively scan directories"
    complete -c $cmd -l exclude -d "Glob pattern to exclude"
    complete -c $cmd -l diff -d "Display syntax-colored unified diff"
    complete -c $cmd -l check -d "Linter/CI check mode"
    complete -c $cmd -l dry-run -d "Report files that would change"
    complete -c $cmd -l json -d "Output results in JSON format"
    complete -c $cmd -l parse -d "Inspect nested function AST"
    complete -c $cmd -l format -x -a "{FORMAT_CHOICES}" -d "Input format"
    complete -c $cmd -l theme -x -a "{THEME_CHOICES}" -d "Curated theme preset"
    complete -c $cmd -s c -l color -d "Override color role"
    complete -c $cmd -l main-color -d "Override main function color"
    complete -c $cmd -l show-colors -l show-palette -d "Display active palette"
    complete -c $cmd -l reset-colors -l reset-palette -d "Restore factory defaults"
    complete -c $cmd -l reset-config -d "Reset local config"
    complete -c $cmd -l init-config -F -d "Generate config template"
    complete -c $cmd -l config -F -d "Custom config path"
    complete -c $cmd -l preset -x -a "{PRESET_CHOICES}" -d "Feature preset"
    complete -c $cmd -l taxonomy -d "Enable taxonomy"
    complete -c $cmd -l no-taxonomy -d "Disable taxonomy"
    complete -c $cmd -l rainbow-delimiters -d "Enable rainbow delimiters"
    complete -c $cmd -l no-rainbow-delimiters -d "Disable rainbow delimiters"
    complete -c $cmd -l variable-data-flow -d "Enable variable data-flow"
    complete -c $cmd -l no-variable-data-flow -d "Disable variable data-flow"
    complete -c $cmd -l units -d "Enable unit disambiguation"
    complete -c $cmd -l no-units -d "Disable unit disambiguation"
    complete -c $cmd -l differentials -d "Enable differentials"
    complete -c $cmd -l no-differentials -d "Disable differentials"
    complete -c $cmd -l braket -d "Enable bra-ket notation"
    complete -c $cmd -l no-braket -d "Disable bra-ket notation"
    complete -c $cmd -l dimensionless -d "Enable dimensionless groups"
    complete -c $cmd -l no-dimensionless -d "Disable dimensionless groups"
    complete -c $cmd -l undo -d "Strip color wrappers back to plain LaTeX"
    complete -c $cmd -l ui -l gui -d "Open graphical window"
    complete -c $cmd -l tutorial -d "Launch terminal tutorial"
    complete -c $cmd -s V -l version -d "Show version"
    complete -c $cmd -s v -l verbose -d "Verbose progress"
    complete -c $cmd -s q -l quiet -d "Suppress output"
    complete -c $cmd -l self-test -d "Run self-test suite"
    complete -c $cmd -l generate-completion -x -a "{SHELL_CHOICES}" -d "Generate completion script"
end
"""


def generate_powershell() -> str:
    flag_list = "\n        ".join(f'"{f}",' for f in ALL_FLAGS)
    return f"""# PowerShell completion for color-math / python-color-math
Register-ArgumentCompleter -Native -CommandName color-math, python-color-math -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)

    $options = @(
        {flag_list}
    )

    $elements = $commandAst.Elements
    $prev = if ($elements.Count -gt 1) {{ $elements[$elements.Count - 1].Extent.Text }} else {{ "" }}

    if ($prev -eq "--theme") {{
        @("{THEME_CHOICES}".Split(" ")) | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
        return
    }}
    if ($prev -eq "--preset") {{
        @("{PRESET_CHOICES}".Split(" ")) | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
        return
    }}
    if ($prev -eq "--format") {{
        @("{FORMAT_CHOICES}".Split(" ")) | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
        return
    }}
    if ($prev -eq "--generate-completion") {{
        @("{SHELL_CHOICES}".Split(" ")) | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
        return
    }}

    $options | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
    }}
}}
"""


def get_completion_script(shell: str) -> str:
    """Return the completion script for the requested shell."""
    shell_lower = shell.strip().lower()
    if shell_lower == "bash":
        return generate_bash()
    elif shell_lower == "zsh":
        return generate_zsh()
    elif shell_lower == "fish":
        return generate_fish()
    elif shell_lower == "powershell":
        return generate_powershell()
    raise ValueError(f"Unsupported shell: '{shell}'. Choose from: {', '.join(SHELLS)}")


generate_completion = get_completion_script
