# Phosphor Icons, duotone (the shell's chrome)

`duotone.svg` holds, one `<symbol id="ph-<name>">` each, the icons the shell
draws in the sidebar, the header and the footer, taken from
`@phosphor-icons/core@2.1.1` (`assets/duotone/<name>-duotone.svg`, MIT, see
`LICENSE.txt`). Each icon keeps its two paths as published; the tinted one
reads its opacity from the skin's `--uvl-icon-duotone-opacity` instead of
the fixed 0.2.

`templates/_uvl_icons.html` translates the feather names the menu registry
and the slots use into these. To add one, take its `-duotone.svg` from the
same release, add a `<symbol>` like the others and a line to the table.
