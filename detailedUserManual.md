## Detailed User Manual

Comprehensive guides and specifications for `api-test-e10`:

### Core Documentation
- **[Core Principles](./doc/core_principles.md)**: Foundational architecture, preflight checks, deduplication, and closed-loop pytest verification.
- **[Coding Style Guide](./doc/coding_style_guide.md)**: API method naming, payload design, return value unpacking, and assertion patterns.
- **[Capture Guide](./capture/README.md)**: Setting up mitmproxy, configuring browser proxies, and capturing API flows.
- **[Troubleshooting & Tips](./doc/high_frequency_experience.md)**: Common traps and high-frequency debugging solutions.

### Authoring Modes
1. **[Mode 1: Capture-Driven](./doc/mode_capture_driven.md)**: Turn UI actions into automated API tests.
2. **[Mode 2: Reference Case](./doc/mode_reference_case.md)**: Mirror existing test cases for new endpoints.
3. **[Mode 3: Manual cURL](./doc/mode_curl_manual.md)**: Generate tests directly from raw cURL requests.
4. **[Mode 4: Java Controller Source](./doc/mode_java_controller_source.md)**: Analyze backend Controller sources or Jacoco coverage reports.
5. **[Mode 5: Maintenance Mode](./doc/mode_maintenance_pytest_driven.md)**: Pytest error-driven test case maintenance.
