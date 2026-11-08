FROM nginx:1.27.5@sha256:6784fb0834aa7dbbe12e3d7471e69c290df3e6ba810dc38b34ae33d3c1c05f7d
COPY nginx/templates/default.prod.conf.template /etc/nginx/templates/default.conf.template

# Location snippets shipped with the deployment. The compose file also bind
# mounts this directory, so snippets added after the build are picked up on
# a restart without rebuilding the image.
COPY nginx/locations/ /etc/nginx/conf.d/locations/

# Renders NGINX_TRUSTED_PROXY_CIDRS into the geo entries and the
# set_real_ip_from lines the server template includes. The empty files
# baked here keep the config valid, and trust no peer, even if the
# entrypoint scripts are ever skipped.
COPY nginx/docker-entrypoint.d/15-splent-trusted-proxies.sh /docker-entrypoint.d/15-splent-trusted-proxies.sh
# Writes the server that redirects NGINX_REDIRECT_SERVER_NAMES to the
# canonical name. Without it the templates include an empty directory.
COPY nginx/docker-entrypoint.d/16-splent-redirects.sh /docker-entrypoint.d/16-splent-redirects.sh
RUN chmod +x /docker-entrypoint.d/15-splent-trusted-proxies.sh \
        /docker-entrypoint.d/16-splent-redirects.sh \
    && mkdir -p /etc/nginx/trusted_proxies /etc/nginx/redirects \
    && touch /etc/nginx/trusted_proxies/trusted.conf /etc/nginx/trusted_proxies/realip.conf
