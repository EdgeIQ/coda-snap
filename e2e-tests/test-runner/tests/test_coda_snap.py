"""
E2E tests for Coda snap installation and configuration
"""

import time
import subprocess
import pytest

MQTT_BROKER_PROTOCOL = "tcp"
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
PLATFORM_URL = "http://localhost:8080/api/v1/platform"

class TestCodaSnapInstallation:
    """Test suite for Coda snap installation and basic functionality"""

    def exec_command(self, vm_name, command, check=True, timeout=300):
        """
        Execute command in Multipass VM and return result

        Args:
            vm_name: Name of the Multipass VM
            command: Command to execute
            check: If True, raise exception on non-zero exit code
            timeout: Command timeout in seconds (default: 300)

        Returns:
            tuple: (exit_code, output)
        """
        print(f"Executing: {command}")
        try:
            result = subprocess.run(
                ['multipass', 'exec', vm_name, '--', 'bash', '-c', command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            exit_code = result.returncode
            output = result.stdout + result.stderr

            print(f"Exit code: {exit_code}")
            print(f"Output: {output}")

            if check and exit_code != 0:
                raise RuntimeError(f"Command failed with exit code {exit_code}: {output}")

            return exit_code, output
        except subprocess.TimeoutExpired:
            print(f"Command timed out after {timeout} seconds")
            raise
        except Exception as e:
            print(f"Command execution failed: {e}")
            raise

    def test_install_coda_snap(self, multipass_vm, wait_for_services, snap_in_vm):
        """Install the coda snap from the snap store or local file"""

        COMPANY_ID = "test-company-001"
        UNIQUE_ID = "test-device-001"

        # Verify snapd is responsive
        print("Verifying snapd is ready...")
        for attempt in range(10):
            exit_code, _ = self.exec_command(
                multipass_vm,
                "snap version",
                check=False
            )
            if exit_code == 0:
                print("✓ snapd is ready")
                break
            print(f"Waiting for snapd (attempt {attempt + 1}/10)...")
            time.sleep(3)

        assert exit_code == 0, "Snapd did not become ready"

        # List installed snaps
        exit_code, output = self.exec_command(
            multipass_vm,
            "snap list"
        )
        print(f"Installed snaps: {output}")

        # Install coda snap - either from local file or store
        if snap_in_vm['source'] == 'local':
            print(f"\n{'='*60}")
            print(f"Installing coda snap from LOCAL FILE")
            print(f"File: {snap_in_vm['file_path']}")
            print(f"{'='*60}\n")

            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo snap install --dangerous {snap_in_vm['file_path']}",
                timeout=120
            )
        else:
            print(f"\n{'='*60}")
            print(f"Installing coda snap from SNAP STORE")
            print(f"Channel: {snap_in_vm['channel']}")
            print(f"{'='*60}\n")

            # Get info from the store about coda snap
            exit_code, output = self.exec_command(
                multipass_vm,
                "snap info coda"
            )
            print(f"Coda snap info: {output}")

            # Install from store
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo snap install coda --channel={snap_in_vm['channel']}",
                timeout=120
            )

        # If installation appears stuck or failed, check snap changes
        if exit_code != 0:
            print("Installation failed, checking snap changes...")
            _, changes_output = self.exec_command(
                multipass_vm,
                "snap changes",
                check=False
            )
            print(f"Snap changes: {changes_output}")

            # Try to get detailed logs
            _, log_output = self.exec_command(
                multipass_vm,
                "snap tasks --last=install",
                check=False
            )
            print(f"Snap task details: {log_output}")

        assert exit_code == 0, f"Failed to install coda snap: {output}"
        assert "coda" in output.lower()

        # Verify installation
        exit_code, output = self.exec_command(
            multipass_vm,
            "snap list"
        )
        assert exit_code == 0
        assert "coda" in output

        print("✓ Coda snap installed successfully")

        # Connect required interfaces
        print("Connecting required snap interfaces...")
        interfaces = [
            "home",
            "shutdown",
            "snapd-control",
            "hardware-observe",
            "system-observe",
            "network",
            "network-bind",
            "network-control",
            "network-manager",
            "network-manager-observe",
            "network-observe",
            "network-setup-control",
            "network-setup-observe",
            "network-status",
            "modem-manager",
            "ppp",
            "firewall-control",
            "tpm",
            "log-observe",
            "physical-memory-observe",
            "mount-observe",
            "ssh-public-keys",
            "raw-usb"
        ]

        for interface in interfaces:
            print(f"Connecting interface: {interface}")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo snap connect coda:{interface} :{interface}",
                check=False
            )
            if exit_code == 0:
                print(f"✓ Connected {interface}")
            else:
                print(f"⚠ Could not connect {interface}: {output}")

        print("✓ Interface connections completed")

        # Configure coda with unique-id and company-id
        print("Configuring coda snap...")
        
        # Set unique-id
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda bootstrap.unique-id={UNIQUE_ID}"
        )
        assert exit_code == 0, f"Failed to set unique-id: {output}"
        print(f"✓ Set bootstrap.unique-id={UNIQUE_ID}")

        # Set company-id
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda bootstrap.company-id={COMPANY_ID}"
        )
        assert exit_code == 0, f"Failed to set company-id: {output}"
        print(f"✓ Set bootstrap.company-id={COMPANY_ID}")

        # Set mqtt broker host & port
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.mqtt.broker.protocol={MQTT_BROKER_PROTOCOL}"
        )
        assert exit_code == 0, f"Failed to set mqtt broker protocol: {output}"
        print(f"✓ Set conf.mqtt.broker.protocol={MQTT_BROKER_PROTOCOL}")

        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.mqtt.broker.host={MQTT_BROKER_HOST}"
        )
        assert exit_code == 0, f"Failed to set mqtt broker host: {output}"
        print(f"✓ Set conf.mqtt.broker.host={MQTT_BROKER_HOST}")

        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.mqtt.broker.port={MQTT_BROKER_PORT}"
        )
        assert exit_code == 0, f"Failed to set mqtt broker port: {output}"
        print(f"✓ Set conf.mqtt.broker.port={MQTT_BROKER_PORT}")

        # Set platform url
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.platform.url={PLATFORM_URL}"
        )
        assert exit_code == 0, f"Failed to set platform url: {output}"
        print(f"✓ Set conf.platform.url={PLATFORM_URL}")

        # Restart coda snap to apply configuration
        print("Restarting coda snap...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap restart coda"
        )
        assert exit_code == 0, f"Failed to restart coda snap: {output}"
        print("✓ Coda snap restarted")

        # Verify configuration
        print("Verifying configuration...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap get coda bootstrap"
        )
        assert exit_code == 0, f"Failed to get configuration: {output}"
        print(f"Bootstrap configuration: {output}")
        assert UNIQUE_ID in output, "unique-id not found in configuration"
        assert COMPANY_ID in output, "company-id not found in configuration"

        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap get coda conf"
        )
        assert exit_code == 0, f"Failed to get configuration: {output}"
        print(f"Configuration: {output}")
        assert MQTT_BROKER_PROTOCOL in output, "mqtt broker protocol not found in configuration"
        assert MQTT_BROKER_HOST in output, "mqtt broker host not found in configuration"
        assert f"{MQTT_BROKER_PORT}" in output, "mqtt broker port not found in configuration"
        assert PLATFORM_URL in output, "platform url not found in configuration"

        print("✓ Coda snap configured successfully")

        # sleep for 10 seconds
        time.sleep(10)

        # Print coda snap logs
        print("Printing coda snap logs...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap logs coda"
        )
        print(f"Coda snap logs: {output}")
        assert exit_code == 0, f"Failed to get logs: {output}"

    def test_disk_space_exhaustion_crash(self, multipass_vm):
        """
        Test that coda snap handles disk space exhaustion gracefully without crashing.

        This test:
        1. Creates a small loop device (10MB)
        2. Mounts it over the common directory
        3. Pre-fills most of the space to create disk constraint
        4. Monitors snap behavior under disk pressure
        5. Verifies snap handles the situation gracefully (no crashes)
        6. Cleans up and verifies snap continues running normally

        Expected graceful behavior:
        - No "no space left on device" errors in logs
        - No snap service crashes or exits
        - No systemd restart loops
        - Snap remains in active/running state
        - Snap may log warnings about disk space but continues operating
        """

        COMMON_DIR = "/var/snap/coda/common"
        COMMON_BACKUP = "/tmp/common_backup"
        LOOP_DEVICE_FILE = "/tmp/loop_disk_test.img"
        LOOP_DEVICE_SIZE_MB = 10  # 10MB - will be filled by restored files + prefill
        MONITOR_DURATION = 60  # Monitor for 60 seconds to verify stable operation

        print("\n" + "="*80)
        print("TEST: Disk Space Exhaustion - Graceful Handling")
        print("="*80)

        try:
            # Step 1: Stop coda snap service
            print("\n[1/9] Stopping coda snap service...")
            exit_code, output = self.exec_command(
                multipass_vm,
                "sudo snap stop coda"
            )
            assert exit_code == 0, f"Failed to stop coda snap: {output}"
            print("✓ Coda snap stopped")

            # Step 2: Backup entire common directory
            print("\n[2/9] Backing up entire common directory...")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo mkdir -p {COMMON_BACKUP} && sudo cp -r {COMMON_DIR}/* {COMMON_BACKUP}/",
                timeout=30
            )
            assert exit_code == 0, f"Failed to backup common directory: {output}"
            print(f"✓ Common directory backed up to {COMMON_BACKUP}")

            # Step 3: Create loop device file
            print(f"\n[3/9] Creating {LOOP_DEVICE_SIZE_MB}MB loop device file...")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"dd if=/dev/zero of={LOOP_DEVICE_FILE} bs=1M count={LOOP_DEVICE_SIZE_MB}",
                timeout=30
            )
            assert exit_code == 0, f"Failed to create loop device file: {output}"
            print(f"✓ Loop device file created: {LOOP_DEVICE_FILE}")

            # Step 4: Format as ext4
            print("\n[4/9] Formatting loop device as ext4...")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo mkfs.ext4 -F {LOOP_DEVICE_FILE}",
                timeout=30
            )
            assert exit_code == 0, f"Failed to format loop device: {output}"
            print("✓ Loop device formatted")

            # Step 5: Mount loop device over entire common directory
            print(f"\n[5/9] Mounting loop device over {COMMON_DIR}...")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo mount -o loop {LOOP_DEVICE_FILE} {COMMON_DIR}",
                timeout=30
            )
            assert exit_code == 0, f"Failed to mount loop device: {output}"
            print(f"✓ Loop device mounted on {COMMON_DIR}")

            # Restore backed up files to loop device
            print("Restoring backed up files...")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo cp -r {COMMON_BACKUP}/* {COMMON_DIR}/",
                timeout=30
            )
            assert exit_code == 0, f"Failed to restore files: {output}"
            print("✓ Files restored to loop device")

            # Verify mount and check disk usage
            exit_code, output = self.exec_command(
                multipass_vm,
                f"df -h {COMMON_DIR}",
                check=False
            )
            print(f"Disk status after restore:\n{output}")

            # Step 6: Pre-fill remaining space to ensure disk is close to 100%
            print(f"\n[6/9] Pre-filling remaining disk space...")
            # Fill to capacity - the dd command will fail when disk is full, which is expected
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo dd if=/dev/zero of={COMMON_DIR}/prefill.dat bs=1M count=50 2>&1 || true",
                timeout=30
            )
            print("✓ Disk filled to capacity")

            # Check final disk usage
            exit_code, output = self.exec_command(
                multipass_vm,
                f"df -h {COMMON_DIR}",
                check=False
            )
            print(f"Final disk usage:\n{output}")

            # Step 7: Start coda snap service (should start successfully despite disk constraints)
            print("\n[7/9] Starting coda snap service (should handle disk constraints gracefully)...")
            exit_code, output = self.exec_command(
                multipass_vm,
                "sudo snap start coda",
                check=False
            )
            print(f"Start command result: {output}")

            # Wait a moment for snap to stabilize
            print("Waiting 5 seconds for snap to stabilize...")
            time.sleep(5)

            # Step 8: Monitor for graceful handling (no crash/error patterns should occur)
            print(f"\n[8/9] Monitoring snap behavior under disk pressure (max {MONITOR_DURATION}s)...")

            # Monitor logs to ensure graceful handling (no errors)
            start_time = time.time()
            found_no_space = False
            found_failed_hook = False
            found_fatal_error = False
            found_exit_failure = False
            restart_count = 0
            loop_iteration = 0
            service_active_count = 0

            while time.time() - start_time < MONITOR_DURATION:
                loop_iteration += 1
                elapsed = int(time.time() - start_time)
                print(f"\n[Monitoring iteration {loop_iteration}, elapsed: {elapsed}s]")

                # Get journalctl logs
                exit_code, output = self.exec_command(
                    multipass_vm,
                    "sudo journalctl -u snap.coda.agent.service -n 100 --no-pager",
                    check=False,
                    timeout=10
                )

                # Check systemctl status
                exit_code_status, status_output = self.exec_command(
                    multipass_vm,
                    "sudo systemctl status snap.coda.agent.service --no-pager -l",
                    check=False,
                    timeout=10
                )

                # Check disk usage on first and every 3rd iteration
                if loop_iteration == 1 or loop_iteration % 3 == 0:
                    exit_code_df, df_output = self.exec_command(
                        multipass_vm,
                        f"df -h {COMMON_DIR} | tail -1",
                        check=False,
                        timeout=10
                    )
                    print(f"Disk usage: {df_output.strip()}")

                # Check for error patterns that should NOT occur
                if "no space left on device" in output.lower():
                    if not found_no_space:
                        found_no_space = True
                        print("✗ ERROR: Found 'no space left on device' error (should not occur)")

                if "Failed to fire hook: write" in output or "failed to fire hook" in output.lower():
                    if not found_failed_hook:
                        found_failed_hook = True
                        print("✗ ERROR: Found 'Failed to fire hook: write' error (should not occur)")

                if 'level=fatal msg="resource temporarily unavailable"' in output:
                    if not found_fatal_error:
                        found_fatal_error = True
                        print("✗ ERROR: Found level=fatal error (should not occur)")

                # Check for exit failure in both journalctl and systemctl status
                if "Main process exited, code=exited, status=1/FAILURE" in output or \
                   "Main process exited, code=exited, status=1/FAILURE" in status_output:
                    if not found_exit_failure:
                        found_exit_failure = True
                        print("✗ ERROR: Found 'Main process exited' message (should not occur)")

                # Check for failed/crashed state in systemctl status
                if "Active: failed" in status_output:
                    if not found_exit_failure:
                        found_exit_failure = True
                        print("✗ ERROR: Service is in failed state (should not occur)")

                # Check for active state (this is what we want)
                if "Active: active" in status_output:
                    service_active_count += 1
                    if service_active_count == 1:
                        print("✓ Service is active/running")

                # Count restart attempts (should not occur)
                restart_matches = output.count("Scheduled restart job, restart counter is at")
                if restart_matches > restart_count:
                    restart_count = restart_matches
                    print(f"✗ ERROR: Restart counter detected: {restart_count} restarts (should not occur)")

                # If we detect any error pattern early, we can exit early to fail faster
                if found_no_space or found_exit_failure or restart_count > 0:
                    print(f"\n✗ ERROR: Detected failure patterns early at {int(time.time() - start_time)}s")
                    break

                time.sleep(5)

            # Print final logs and status for debugging
            print("\n[Final systemctl status]")
            exit_code_status, status_output = self.exec_command(
                multipass_vm,
                "sudo systemctl status snap.coda.agent.service --no-pager -l",
                check=False
            )
            print(status_output)

            print("\n[Final logs from journalctl]")
            exit_code, output = self.exec_command(
                multipass_vm,
                "sudo journalctl -u snap.coda.agent.service -n 50 --no-pager",
                check=False
            )
            print(output)

            # Verify we observed graceful handling (no error patterns)
            print("\n[Verification Results]")
            print(f"  - Found 'no space left on device': {found_no_space} (should be False)")
            print(f"  - Found 'Failed to fire hook': {found_failed_hook} (should be False)")
            print(f"  - Found level=fatal error: {found_fatal_error} (should be False)")
            print(f"  - Found exit failure: {found_exit_failure} (should be False)")
            print(f"  - Restart count: {restart_count} (should be 0)")
            print(f"  - Service was active: {service_active_count > 0} (should be True)")

            # Assert on graceful handling - no error patterns should occur
            # Test fails if ANY error pattern is detected
            assert not found_no_space, \
                "FAILED: Found 'no space left on device' error - snap should handle disk constraints gracefully"

            assert not found_failed_hook, \
                "FAILED: Found 'Failed to fire hook' error - snap should handle disk constraints gracefully"

            assert not found_fatal_error, \
                "FAILED: Found level=fatal error - snap should handle disk constraints gracefully"

            assert not found_exit_failure, \
                "FAILED: Found exit failure - snap should remain running under disk pressure"

            assert restart_count == 0, \
                f"FAILED: Found {restart_count} restart(s) - snap should not crash and restart"

            # Service should have been active during monitoring
            assert service_active_count > 0, \
                "FAILED: Service was never active - snap should remain running under disk pressure"

            print("\n✓ Disk space exhaustion handled gracefully - snap remained stable - test passed!")

        finally:
            # Step 9: CLEANUP (critical - must happen even if test fails)
            print("\n[9/9] CLEANUP: Restoring normal operation...")

            # Stop snap
            print("  - Stopping coda snap...")
            self.exec_command(
                multipass_vm,
                "sudo snap stop coda",
                check=False,
                timeout=30
            )

            # Unmount loop device from common directory
            print(f"  - Unmounting loop device from {COMMON_DIR}...")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo umount {COMMON_DIR}",
                check=False,
                timeout=30
            )
            if exit_code == 0:
                print("  ✓ Loop device unmounted")
            else:
                print(f"  ⚠ Failed to unmount: {output}")
                # Force unmount if normal unmount fails
                print("  - Attempting force unmount...")
                self.exec_command(
                    multipass_vm,
                    f"sudo umount -f {COMMON_DIR}",
                    check=False,
                    timeout=30
                )

            # Remove loop device file
            print(f"  - Removing loop device file {LOOP_DEVICE_FILE}...")
            self.exec_command(
                multipass_vm,
                f"sudo rm -f {LOOP_DEVICE_FILE}",
                check=False,
                timeout=30
            )
            print("  ✓ Loop device file removed")

            # Restore backed up common directory
            print(f"  - Restoring original common directory from {COMMON_BACKUP}...")
            self.exec_command(
                multipass_vm,
                f"sudo mkdir -p {COMMON_DIR} && sudo cp -r {COMMON_BACKUP}/* {COMMON_DIR}/ 2>/dev/null || true",
                check=False,
                timeout=30
            )
            print("  ✓ Common directory restored")

            # Remove backup
            self.exec_command(
                multipass_vm,
                f"sudo rm -rf {COMMON_BACKUP}",
                check=False
            )

            # Start snap normally
            print("  - Starting coda snap normally...")
            exit_code, output = self.exec_command(
                multipass_vm,
                "sudo snap start coda",
                check=False,
                timeout=30
            )
            print(f"  Start result: {output}")

            # Wait for snap to stabilize
            time.sleep(5)

            # Verify snap is running normally
            print("  - Verifying snap is running normally...")
            exit_code, output = self.exec_command(
                multipass_vm,
                "snap services coda",
                check=False
            )
            print(f"  Snap services status:\n{output}")

            # Check if snap is active
            if "active" in output.lower():
                print("  ✓ Coda snap is running normally after cleanup")
            else:
                print("  ⚠ Coda snap may not be running normally")
                # Print recent logs for debugging
                self.exec_command(
                    multipass_vm,
                    "sudo snap logs coda -n=20",
                    check=False
                )

            print("\n✓ CLEANUP COMPLETE")
            print("="*80)
