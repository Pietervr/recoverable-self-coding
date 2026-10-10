#!/bin/bash
# stub ssh for test_pull_tree.py: runs the remote command locally. STUB_SSH_MODE: ok | truncate | hang
for last; do :; done
case "${STUB_SSH_MODE:-ok}" in
  ok) exec sh -c "$last" ;;
  truncate) sh -c "$last" | head -c 200000; exit 0 ;;
  hang) sleep 60 ;;
esac
