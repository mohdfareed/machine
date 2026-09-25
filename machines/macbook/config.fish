# Add local development commands.
fish_add_path --path "$DEV_BIN"

function profile -a cmd --description 'Profile a command with GNU time'
    set -l help 'Usage: profile COMMAND [ARGS...]'

    if not set -q argv[1]
        echo "$help" >&2; return 2
    end

    switch "$cmd"
        case -h --help; echo $help; return 0
    end

    # Find the executable.
    set -l executable (command --search -- "$cmd"); or begin
        printf 'profile: external command not found: %s\n' "$cmd" >&2
        return 127
    end

    # Calculate the size of the executable in MiB.
    set -l size_kib (du -Lsk "$executable" | cut -f1)
    set -l size_mib (math --scale=1 "$size_kib / 1024")

    # Define the report template.
    set -l format "\
 Elapsed: %es
 Memory:  %M KB peak
 Size:    $size_mib MiB
 CPU:     %P |  %Us |  %Ss"

    # Profile the command.
    command gtime -f $format -- $argv
end
