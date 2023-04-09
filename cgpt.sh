#!/usr/bin/env sh

# Define functions for macOS and Linux commands
macos_commands() {
    printf "Hostname:%s\nUser:%s\n" "$(hostname)" "$(whoami)"

    printf "resolv.conf:"
    cat /etc/resolv.conf | grep -v "^#"
    printf "\n"

    printf "Diskutil:"
    diskutil list
    printf "\n"

    printf "system_profiler:"
    system_profiler SPSoftwareDataType SPHardwareDataType
    printf "\n"
}

linux_commands() {
    printf "Shell:%s\nLSB:" "$(echo "$SHELL")"
    lsb_release -a | grep -E 'Distributor ID:|Description:|Release:|Codename:'
    printf "Hostname:%s\nUsername:%s\n" "$(hostname)" "$(whoami)"

    printf "Journal:"
    journalctl -n 20 -p 3 --no-tail --no-pager
    printf "\n"

    printf "Resolv.conf:"
    cat /etc/resolv.conf | grep -v "^#"
    printf "\n"

    printf "fstab:"
    cat /etc/fstab | grep -v "^#"
    printf "\n"

    printf "IP:"
    ip -br addr show
    printf "\n"

    printf "LSPCI:"
    lspci | grep -vE "System peripheral|Performance counters|PCI bridge|USB controller|SATA controller|Communication controller|PIC|Serial Attached SCSI|ISA bridge|SMBus"
    printf "\n"

    printf "LSBLK:"
    lsblk -d --output name,size --noheadings --bytes | awk "{printf \"%s %0.2fG\\n\", \$1, \$2/(1024*1024*1024)}"
    printf "\n"
}

tempfile=$(mktemp /tmp/cgpt.XXXXXX)

# Determine the operating system and call the appropriate function
os_name="$(uname)"
if [ "$os_name" = "Darwin" ]; then
    output=$(macos_commands)
else
    output=$(linux_commands)
fi

# Pass the output to another script
python cgpt.py --tempfile "$tempfile" --context "$output"

selected_command=$(<$tempfile)
rm $tempfile

eval $selected_command