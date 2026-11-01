#!/bin/sh
# Write the server that redirects the site's other names to its canonical
# one. The server templates include every file of the output directory.
#
#   redirects.conf  a server for NGINX_REDIRECT_SERVER_NAMES that answers
#                   301 to <scheme>://<canonical><path and query>, where
#                   the canonical name is the first of NGINX_SERVER_NAME.
#
# NGINX_REDIRECT_SERVER_NAMES holds names separated by spaces or commas,
# for example "uvlhub.io old.uvlhub.io", and is empty by default. Empty
# means the file stays empty and every other name gets the default server.
# A name with anything but letters, digits, dots, dashes and a leading
# "*." stops the container, and so does a canonical name nginx would read
# as a pattern: the file goes into nginx's configuration as it is.
#
# SPLENT_REDIRECTS_DIR moves the output, which the feature's tests use;
# the templates read /etc/nginx/redirects.
set -e

out_dir=${SPLENT_REDIRECTS_DIR:-/etc/nginx/redirects}
conf="$out_dir/redirects.conf"

mkdir -p "$out_dir"
: > "$conf"

names=$(printf '%s' "${NGINX_REDIRECT_SERVER_NAMES:-}" | tr ',;' '  ')
set -- $names
[ $# -eq 0 ] && exit 0

for name in "$@"; do
    case "$name" in
        *[!A-Za-z0-9.*-]*|'')
            echo "16-splent-redirects.sh: '$name' in NGINX_REDIRECT_SERVER_NAMES is not a host name" >&2
            exit 1 ;;
    esac
done

canonical=$(printf '%s' "${NGINX_SERVER_NAME:-}" | tr ',;' '  ' | awk '{print $1}')
case "$canonical" in
    ''|_|*[!A-Za-z0-9.-]*)
        echo "16-splent-redirects.sh: the first name of NGINX_SERVER_NAME ('$canonical') is where the other names are sent, so it must be a plain host name" >&2
        exit 1 ;;
esac

cat > "$conf" <<CONF
server {
    listen 80;
    server_name $*;
    access_log /var/log/nginx/access.log splent;

    return 301 \$forwarded_proto://$canonical\$request_uri;
}
CONF
echo "16-splent-redirects.sh: redirecting $* to $canonical"
