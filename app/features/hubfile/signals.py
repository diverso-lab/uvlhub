from splent_framework.signals.signal_utils import define_signal

# Emitted right after a Hubfile row is inserted. The generic hub announces the
# event; domain features (UVL processing, fact labels, ...) subscribe without the
# hub ever importing them. This keeps the dependency arrow domain -> hub.
hubfile_created = define_signal("hubfile-created", "hubfile")
