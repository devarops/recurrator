#shellcheck shell=sh

Describe 'src/create_config.sh'
  setup() {
    work="$SHELLSPEC_TMPBASE/work"
    rm -rf "$work"
    mkdir -p "$work/recurrator" "$work/tests/data"
    cd "$work" || return 1
  }
  BeforeEach 'setup'

  It 'ignores tests/data/config.json when the config path does not exist'
    printf '%s' '{"wip_limit": 42}' > tests/data/config.json

    When run "$SHELLSPEC_PROJECT_ROOT/src/create_config.sh" "$work/missing.json"

    The status should be success
    The contents of file "recurrator/_config.py" should include 'WIP_LIMIT = 6'
  End
End
