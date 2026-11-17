# Open Pattern Quarry on your iPhone with Tailscale

Your Mac hosts the app and database. The iPhone uses Safari over a private Tailscale HTTPS connection; it does not keep a separate database.

The source is available at [AlbionZeglin/PatternQuarry](https://github.com/AlbionZeglin/PatternQuarry). Follow the clone instructions in [QUICKSTART.md](QUICKSTART.md) first if the app has not been installed on the Mac. A Tailscale connection alone does not install or start the app.

## On your Mac

1. Install/update [Tailscale for Mac](https://tailscale.com/download/mac), open it, sign in, and connect.
2. Open Terminal in the updated Pattern Quarry folder and run:

   ```sh
   python3 iphone.py
   ```

   Or run `bash connect-iphone.command`. The launcher automatically finds the Mac app's CLI, your Mac's Tailscale DNS name, and its owner login. No API key, auth key, password file, or manual hostname is needed.
3. If Tailscale asks you to enable HTTPS/Serve, follow the setup link it prints and then rerun the command if needed. Your tailnet administrator may need to enable [MagicDNS and HTTPS certificates](https://tailscale.com/docs/how-to/set-up-https-certificates).
4. Wait for Tailscale to report that the service is available. The launcher prints your exact address, of the form **`https://your-mac.your-tailnet.ts.net:8443`**. Keep Terminal open and the Mac awake. To prevent idle sleep while using it, run `caffeinate -i python3 iphone.py` instead; closing a MacBook lid can still stop access.

## On your iPhone

1. Install [Tailscale for iOS](https://tailscale.com/download/ios), sign in with the **same Tailscale login as your Mac**, allow the VPN configuration, and connect.
2. In Safari, open the exact HTTPS address printed on the Mac, including **`:8443`**. `localhost` on the phone refers to the phone, so use the printed address.
3. You should see the same project and saved sessions. Optionally use Safari's **Share → Add to Home Screen**.

This step must be performed on your devices. The build workspace has no connection to your Mac or iPhone, so a real Tailscale connection has not been established or verified here.

## Updating without losing interviews

The update ZIP excludes the database. If you unzip into a **new folder**, stop the old app and copy its entire `data` folder into the updated folder before launching. Keep the original folder as a backup. If you update source files in place, leave `data/studio.sqlite3` untouched. The launcher uses that same database and makes no schema changes.

## Stop, resume, and troubleshoot

- **Stop:** press Control-C in the launcher Terminal. This stops its backend and foreground Tailscale Serve session. It does not reset other Tailscale services or delete data. Rerun the launcher to resume.
- **Can't reach the address:** confirm Tailscale is connected on both devices, the Mac is awake, and Serve reports the address as available. A work/school tailnet may need its administrator to allow iPhone → Mac TCP **8443**. No router port forwarding is required.
- **Access denied:** both devices must use the same exact login. Membership of the same tailnet alone does not grant access. Tagged devices have no user identity and are rejected.
- **Port already configured:** the launcher refuses to overwrite it. Use another free HTTPS port, e.g. `python3 iphone.py --https-port 9443`, and open the new printed URL. Your tailnet policy must permit that port too. A conflicting local backend port can be changed with `--port 18766`.
- **Tailscale CLI not found:** the launcher checks your PATH and the standard Mac app locations. If installed elsewhere, run `python3 iphone.py --tailscale-bin '/path/to/Tailscale'`.
- **Browser shows old content or a token error:** refresh the page after restarting the launcher.

## Access boundary

The launcher runs the guarded backend on **127.0.0.1:18765** and private **Tailscale Serve** HTTPS on port **8443**. It uses a foreground session, never Funnel, never resets your Serve configuration, and never changes your tailnet ACLs. Other users in the tailnet are denied by the app even if network policy lets them reach the URL. The allowed login can access the **whole private workspace**, including private notes and exports; this is not a shared reviewer portal.

In Tailscale mode all routes require Serve's owner identity and HTTPS proxy headers, including localhost requests. This is separate from the ordinary `python3 server.py` mode, which remains localhost-only and rejects reverse-proxy headers. Local processes on the Mac are trusted; they already have access to the database. Do not expose the backend through another proxy, Funnel, a public listener, or router forwarding.

The Mac database remains unencrypted by this app. Tailscale encrypts the device connection; it does not change the app's publication rules or provide encrypted storage. Author/reviewer fields remain recorded assertions, not per-user roles.

Implementation references: [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve), including its identity-header guarantees, and [Serve CLI](https://tailscale.com/docs/reference/tailscale-cli/serve).
