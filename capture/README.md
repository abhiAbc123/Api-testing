# capture - Packet Capture Base User Guide

> Target Audience: Testers using this Skill for the first time; easy to follow even with zero mitmproxy experience.

## 1. Environment Preparation

### 1.1 Python

```bat
python --version
```

Requires Python 3.8 or above.

### 1.2 Install mitmproxy

```bat
pip install mitmproxy
```

Verify installation:

```bat
mitmdump --version
```

If you see `Mitmproxy: x.y.z`, installation succeeded.

## 2. First Launch (Manual)

### 2.1 Double-click `start.bat`

Or via command line:

```bat
cd api-test-E10\capture
mitmdump -s capture_addon.py --listen-port 12138
```

### 2.2 Successful logs should look like:

```
[api-test-E10] self.baseurl = weapp.mulinquan.cn
[api-test-E10] self.prefixes = ['/api/', '/sapi/', ...]
[api-test-E10] self.jsonl_path = ...\api_test_dwp_temp\latest.jsonl
Proxy server listening at *:12138
```

**If `self.baseurl = <empty>`**: It means `config.py` was not found, or its `RunConfig.baseurl` was commented out. Please verify that the active baseurl in config.py is not commented out.
After startup, the addon synchronizes the resolved `RunConfig.baseurl` into the `baseurl` field of `config.json` via `skill_utils/common_function.py`.

## 3. Install CA Certificate (Crucial Step)

mitmproxy requires installing its root certificate into Windows Trusted Root Certification Authorities to decrypt HTTPS traffic.

### 3.1 Download Certificate

1. Start mitmdump (Step 2)
2. Configure browser proxy to `127.0.0.1:12138` (Step 4)
3. Visit `http://mitm.it` in the browser
4. Click the **Windows** icon to download `mitmproxy-ca-cert.p12`

### 3.2 Install to "Local Machine"

1. Double-click `mitmproxy-ca-cert.p12`
2. Select **Local Machine** (NOT "Current User")
3. Proceed through the wizard
4. On "Certificate Store", select **Place all certificates in the following store** -> **Browse** -> **Trusted Root Certification Authorities** -> OK
5. Finish -> Import successful

### 3.3 Verification

Visit any HTTPS website; there should be no "Certificate Not Trusted" warning.

## 4. Configure Browser Proxy

### Recommended: Chrome + SwitchyOmega Extension

1. Install SwitchyOmega from Chrome Web Store
2. Create profile "mitm"
   - Proxy Protocol: HTTP
   - Server: `127.0.0.1`
   - Port: `12138`
3. Switch to "mitm" when capturing, and switch back to "Direct" when done

### Alternative: Windows System Proxy

**Windows Settings -> Network & Internet -> Proxy -> Manual proxy setup**:
- Address: `127.0.0.1`
- Port: `12138`
- Enable

**Note**: System proxy affects all HTTP clients (pip, git, desktop apps). Turn it off when finished.

## 5. Verify Capture Pipeline

1. Proxy enabled (Step 4)
2. mitmdump running (Step 2)
3. Open target environment in browser and execute any business operation
4. Check `api_test_dwp_temp/latest.jsonl`:
   - Under project root directory, run: `type api_test_dwp_temp\latest.jsonl`
   - Seeing multiple lines of JSON confirms success

Key JSON fields:

| Field | Meaning |
|---|---|
| `ts` / `epoch` | Capture timestamp |
| `method` / `url` / `path` | HTTP request |
| `req_headers` | Request headers (Cookie/Authorization digested) |
| `req_body` | Request body (text) |
| `status` | HTTP status code |
| `resp_body` | Response body (binary skipped) |
| `body_skipped` / `skip_reason` | Binary/encoded response flags |
| `is_login` | Login/logout endpoint tag |

## 6. AI Assistance Mode (Recommended)

After setting up certificate and browser proxy, ask Claude Code / AI:

> "Help me start api-test-E10 capture"

The AI will:
1. Run `tools/check_capture_server.py` to inspect port 12138
2. Call `start.bat` if not running
3. Wait for port LISTENING
4. Report `self.baseurl`, `self.prefixes`, `self.jsonl_path`, and notify that capture is ready

To force cleanup of old processes and restart, say "Restart capture service". The AI will run `capture/restart.bat`.

**Steps requiring user manual GUI action**:
- Double-clicking certificate and accepting Windows trust prompt
- Installing SwitchyOmega extension in the browser

## 7. Extend Filter Prefixes

Default captured path prefixes:

```
/api/  /sapi/  /base/  /papi/  /ipconfigrec/  /tenantlogo/  /app/
```

To add more, edit `allowed_prefixes.txt`, one per line.
Restart mitmdump after modifications (`restart.bat`).

## 8. Stop Capture

- Option A: Press `Ctrl+C` in mitmdump window
- Option B: Double-click `stop.bat`
- Option C: Let AI run `stop.bat`

## 9. FAQ

**Q: `pip install mitmproxy` fails with SSL error?**
A: Check if a system proxy is active. Disable proxy before installing, or use an internal mirror.

**Q: `start.bat` flashes and closes?**
A: Run `mitmdump -s capture_addon.py --listen-port 12138` directly in terminal to inspect errors (usually Python environment or version mismatch).

**Q: Port 12138 already occupied?**
A: Run `stop.bat`. If the process is not mitmdump, check PID with `netstat -ano | findstr :12138` and handle accordingly.

**Q: Certificate installed but still shows security warnings?**
A: Usually installed to "Current User" instead of "Local Machine". Repeat Step 3.2.

**Q: Cannot capture requests under `/oa/second`?**
A: Check `config.py` and ensure `RunConfig.baseurl` matches the accessed domain. The addon only captures requests matching `baseurl`.

**Q: HTTPS website access fails?**
A: Verify certificate installation, proxy settings, and that mitmdump is running.

**Q: Are cookies visible in captures?**
A: Cookie and Authorization headers in `req_headers` are digested (first 20 chars + length). Full response bodies are captured, so periodically clean `latest.jsonl`.

**Q: Are file download response bodies captured?**
A: For binary content-types (octet-stream, pdf, zip, image/*, etc.), bodies are skipped automatically (`body_skipped: true`).

## 10. Runtime Files and Cleanup

| File | Description | Version Controlled |
|---|---|---|
| `api_test_dwp_temp/latest.jsonl` | Captured records (project root) | No |
| `tools/page_api_index.sqlite3` | Global API coverage index (skill) | Yes |
| `api_test_dwp_temp/capture_selection.md` | Draft selection (project root) | No |

`api_test_dwp_temp/` is automatically created at project root on first tool run.
It is recommended to delete `latest.jsonl` after completing test case authoring.
