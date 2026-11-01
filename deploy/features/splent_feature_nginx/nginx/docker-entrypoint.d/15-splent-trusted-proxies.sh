#!/bin/sh
# Build the files that decide which peers this server believes. The
# server templates include both.
#
#   trusted.conf  geo entries: a listed peer may assert X-Forwarded-Proto,
#                 X-Forwarded-Host and X-Request-ID.
#   realip.conf   set_real_ip_from lines: a listed peer may name the client
#                 in X-Forwarded-For, which then becomes $remote_addr, so
#                 the rate limits, the access log and the address the app
#                 is told about are the client's and not the peer's.
#
# NGINX_TRUSTED_PROXY_CIDRS holds a comma or space separated list of CIDRs,
# for example "172.16.0.0/12, 127.0.0.1/32", and is empty by default. Empty
# means both files stay empty, no peer is trusted, the forwarded headers
# are rewritten from $scheme and $host and the peer is the client. Only a
# host-level TLS terminator in front of this container justifies filling
# it in.
#
# SPLENT_TRUSTED_PROXIES_DIR moves the output, which the feature's tests
# use; the templates read /etc/nginx/trusted_proxies.
set -e

out_dir=${SPLENT_TRUSTED_PROXIES_DIR:-/etc/nginx/trusted_proxies}
trusted="$out_dir/trusted.conf"
realip="$out_dir/realip.conf"

mkdir -p "$out_dir"
: > "$trusted"
: > "$realip"

for cidr in $(printf '%s' "${NGINX_TRUSTED_PROXY_CIDRS:-}" | tr ',;' '  '); do
    printf '%s 1;\n' "$cidr" >> "$trusted"
    printf 'set_real_ip_from %s;\n' "$cidr" >> "$realip"
    echo "15-splent-trusted-proxies.sh: trusting forwarded headers from $cidr"
done
