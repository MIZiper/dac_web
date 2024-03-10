# TODO: change to Makefile

# build frontend

# build
podman build -t dac_web:latest .

# run
#   make sure "podman.sock" exists
#   else `systemctl --user enable --now podman.socket`
podman run --rm -it -p 5000:5000 -v $XDG_RUNTIME_DIR/podman/podman.sock:/run/podman/podman.sock dac_web:latest

# debug
podman run --rm -it --entrypoint bash dac_web:latest