#!/bin/bash
set -e
export DISPLAY=:99
rm -f /tmp/.X99-lock
rm -f /tmp/.X11-unix/X99
Xvfb :99 -screen 0 1366x768x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!
sleep 2
if ! kill -0 $XVFB_PID 2>/dev/null; then
    echo "Xvfb failed to start"
    exit 1
fi
echo "Xvfb running on DISPLAY=$DISPLAY (PID=$XVFB_PID)"
exec "$@"
