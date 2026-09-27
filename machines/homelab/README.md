# Homelab

## Storage and startup

The M1 keeps databases and app state locally at `MC_HOMELAB_STORAGE_DIR`;
the PC supplies bulk media over SMB. Storage paths are set in `machine.py`.
Both machines must remain awake for continuous media access.

1. Connect in Finder to `smb://<PC-LAN-address>/Media` using the owning Windows
   account's network credentials, not a Windows Hello PIN. Save credentials in
   Keychain. The share must mount at `MC_HOMELAB_MEDIA_DIR` (`/Volumes/Media`),
   not a similarly named local folder.
2. Verify the mount is writable and contains `movies`, `series`, `anime`, and
   `downloads`. Docker Desktop must be able to access both storage paths.
3. Finish Docker Desktop's first launch and enable its start-at-sign-in setting.
   Verify SMB reconnection and Docker startup after PC sleep/reboot and M1 restart
   before relying on availability. FileVault can require a local unlock after reboot.

Deploy on the M1 after reviewing the configuration and completing service setup:

```sh
mc deploy -m homelab
```

## macOS settings

After every deployment, review **System Settings -> General -> Sharing**:

- **Remote Login:** allowed users and remote-user Full Disk Access as needed.
- **Remote Management:** your account and required privileges.
- **File Sharing:** shared folders and permissions; enable Windows File Sharing
  and a Time Machine destination only if those are being used.

Configure native macOS updates in **System Settings -> General -> Software Update
-> Automatic Updates**. They are independent of `mc upgrade`.
