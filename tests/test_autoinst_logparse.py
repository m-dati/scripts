import pytest
from autoinst_logparse import remove_lines

test_str = r'''
[2020-02-05T20:43:40.0274 CET] [info] [pid:32771] +++ setup notes +++
[2020-02-05T20:43:40.0275 CET] [info] [pid:32771] Start time: 2020-02-05 19:43:40
[2020-02-05T20:44:20.0848 CET] [info] [pid:32771] Download of SLES-15-SP2-x86_64-Build136.2-wicked.qcow2 processed:
[info] [#268521] Cache size of "/var/lib/openqa/cache" is 49GiB, with limit 50GiB
[info] [#268521] Downloading "SLES-15-SP2-x86_64-Build136.2-wicked.qcow2" from "http://openqa.suse.de/tests/3867902/asset/hdd/SLES-15-SP2-x86_64-Build136.2-wicked.qcow2"
[2020-02-05T20:44:31.0002 CET] [info] [pid:32771] Rsync from 'rsync://openqa.suse.de/tests' to '/var/lib/openqa/cache/openqa.suse.de', request #268523 sent to Cache Service
[2020-02-05T20:44:36.0084 CET] [info] [pid:32771] Output of rsync:
[info] [#268523] Calling: rsync -avHP rsync://openqa.suse.de/tests/ --delete /var/lib/openqa/cache/openqa.suse.de/tests/
receiving incremental file list
sle/.git/
sle/.git/FETCH_HEAD

              0   0%    0.00kB/s    0:00:00
          3,098 100%    2.95MB/s    0:00:00 (xfr#1, ir-chk=1019/1053)
[2020-02-05T20:44:36.0100 CET] [debug] [pid:61537] Start time: 2020-02-05 19:44:36
[2020-02-05T20:44:36.677 CET] [debug] usingenv DESKTOP=textmode
[2020-02-05T20:44:36.677 CET] [debug] usingenv TEXTMODE=1
[2020-02-05T20:44:39.371 CET] [debug] {
    "virtual-size": 32212254720,
    "filename": "/var/lib/openqa/pool/19/SLES-15-SP2-x86_64-Build136.2-wicked.qcow2",
[2020-02-05T20:44:39.420 CET] [debug] Waiting for 0 attempts
[2020-02-05T20:44:40.421 CET] [debug] Waiting for 1 attempts
[2020-02-05T20:44:41.422 CET] [debug] Finished after 2 attempts
[2020-02-05T20:44:41.627 CET] [debug] Snapshots are supported
[2020-02-05T20:44:41.629 CET] [debug] ||| starting boot_to_desktop tests/boot/boot_to_desktop.pm
[2020-02-05T20:44:41.634 CET] [debug] /var/lib/openqa/cache/openqa.suse.de/tests/sle/tests/boot/boot_to_desktop.pm:42 called opensusebasetest::wait_boot
[2020-02-05T20:44:41.634 CET] [debug] <<< testapi::assert_screen(mustmatch=[
  "linux-login",
  "emergency-shell",
  "emergency-mode"
], timeout=300)
[2020-02-05T20:44:43.021 CET] [debug] no match: 299.0s, best candidate: installation-autoyast-linuxlogin-20171204 (0.29)
[2020-02-05T20:44:43.793 CET] [debug] no match: 298.0s, best candidate: installation-autoyast-linuxlogin-20171204 (0.29)
[2020-02-05T20:44:44.740 CET] [debug] no match: 297.0s, best candidate: installation-autoyast-linuxlogin-20171204 (0.29)
[2020-02-05T20:44:45.616 CET] [debug] no change: 296.0s
[2020-02-05T20:44:46.027 CET] [debug] pointer type 1 0 800 600 -257
[2020-02-05T20:44:49.133 CET] [debug] WARNING: check_asserted_screen took 2.52 seconds for 29 candidate needles - make your needles more specific
[2020-02-05T20:44:49.133 CET] [debug] no match: 295.0s, best candidate: installation-autoyast-linuxlogin-20171204 (0.29)
[2020-02-05T20:44:49.370 CET] [debug] no match: 292.4s, best candidate: linux-login-bsc1055103-20170822 (0.00)
[2020-02-05T20:44:50.357 CET] [debug] no match: 291.5s, best candidate: linux-login-bsc1055103-20170822 (0.00)
[2020-02-05T20:44:56.008 CET] [debug] WARNING: check_asserted_screen took 4.87 seconds for 29 candidate needles - make your needles more specific
[2020-02-05T20:44:56.009 CET] [debug] no match: 290.4s, best candidate: linux-login-bsc1055103-20170822 (0.00)
[2020-02-05T20:45:06.013 CET] [debug] WARNING: check_asserted_screen took 9.98 seconds for 29 candidate needles - make your needles more specific
[2020-02-05T20:45:06.013 CET] [debug] no match: 285.6s, best candidate: linux-login-bsc1055103-20170822 (0.00)
[2020-02-05T20:45:06.017 CET] [debug] WARNING: There is some problem with your environment, we detected a stall for 10.0026431083679 seconds
[2020-02-05T20:45:06.025 CET] [debug] no change: 275.6s
[2020-02-05T20:45:07.291 CET] [debug] >>> testapi::_handle_found_needle: found autoyast-system-login-console-sles11sp4-20180131, similarity 1.00 @ 80/124
[2020-02-05T20:45:07.296 CET] [debug] ||| finished boot_to_desktop boot at 2020-02-05 19:45:07 (26 s)
[2020-02-05T20:45:07.818 CET] [debug] EVENT {"data":{"status":"active"},"event":"MIGRATION","timestamp":{"microseconds":322515,"seconds":1580931907}}
[2020-02-05T20:45:07.818 CET] [debug] Migrating total bytes:     	1091641344
[2020-02-05T20:45:07.818 CET] [debug] Migrating remaining bytes:   	1066917888
[2020-02-05T20:45:08.319 CET] [debug] Migrating total bytes:     	1091641344
[2020-02-05T20:45:08.319 CET] [debug] Migrating remaining bytes:   	949858304
[2020-02-05T20:45:08.820 CET] [debug] Migrating total bytes:     	1091641344
[2020-02-05T20:45:17.973 CET] [debug] ||| starting locks_init tests/wicked/locks_init.pm
[2020-02-05T20:45:17.981 CET] [debug] QEMU: Formatting '/var/lib/openqa/pool/19/raid/hd0-overlay1', fmt=qcow2 size=32212254720 backing_file=/var/lib/openqa/pool/19/raid/hd0-overlay0 backing_fmt=qcow2 cluster_size=65536 lazy_refcounts=off refcount_bits=16
[2020-02-05T20:45:17.982 CET] [debug] /var/lib/openqa/cache/openqa.suse.de/tests/sle/tests/wicked/locks_init.pm:39 called lockapi::mutex_wait
[2020-02-05T20:44:41.634 CET] [debug] /var/lib/openqa/cache/openqa.suse.de/tests/sle/tests/boot/boot_to_desktop.pm:42 called opensusebasetest::wait_boot
[2020-02-05T20:45:17.982 CET] [debug] <<< testapi::record_info(title="Paused", output="Wait for wicked_barriers_created (on parent job)", result="ok")
[2020-02-05T20:45:18.050 CET] [debug] /var/lib/openqa/cache/openqa.suse.de/tests/sle/tests/wicked/locks_init.pm:39 called lockapi::mutex_wait
[2020-02-05T20:45:18.050 CET] [debug] <<< testapi::record_info(title="Paused 0m1s", output="Wait for wicked_barriers_created (on parent job)", result="ok")
[2020-02-05T20:45:18.051 CET] [debug] ||| finished locks_init wicked at 2020-02-05 19:45:18 (1 s)
[2020-02-05T20:45:18.052 CET] [debug] ||| starting before_test tests/wicked/before_test.pm
[2020-02-05T20:45:18.053 CET] [debug] <<< testapi::select_console(testapi_console="root-virtio-terminal")
[2020-02-05T20:45:18.764 CET] [info] ::: consoles::serial_screen::read_until: Matched output from SUT in 3 loops & 0.0264880210161209 seconds: 567uR-0-
[2020-02-05T20:45:18.765 CET] [debug] >>> testapi::wait_serial: (?^:567uR-\d+-): ok
[2020-02-05T20:45:18.765 CET] [debug] <<< testapi::script_run(cmd="wicked show-config > /tmp/before_test_pre/wicked_config.log 2>&1", timeout=undef, quiet=1, output="")
[2020-02-05T20:45:18.766 CET] [debug] <<< testapi::wait_serial(regexp="# ", quiet=1, timeout=90, buffer_size=undef, record_output=undef, no_regex=1, expect_not_found=0)
[2020-02-05T20:44:41.634 CET] [debug] /var/lib/openqa/cache/openqa.suse.de/tests/sle/tests/boot/boot_to_desktop.pm:42 called opensusebasetest::wait_boot
[2020-02-05T20:45:18.766 CET] [debug] <<< consoles::serial_screen::read_until(buffer_size=undef, timeout=90, regexp="# ", expect_not_found=0, no_regex=1, json_cmd_token="XesKuVwt", quiet=1, pattern=[
  "# "
], cmd="backend_wait_serial", record_output=undef)
[2020-02-05T20:45:18.766 CET] [info] ::: consoles::serial_screen::read_until: Matched output from SUT in 2 loops & 0.00032154843211174 seconds: #
[2020-02-05T20:45:18.767 CET] [debug] >>> testapi::wait_serial: # : ok
'''


def test_remove_lines():
    lines = test_str.split('\n')
    filtered_lines = remove_lines(lines)
    assert len(filtered_lines) == 48
