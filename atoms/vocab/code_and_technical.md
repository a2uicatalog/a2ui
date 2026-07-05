---
category: code_and_technical
title: Code & Technical Reference
atom_count: 21
platform_support:
  web: 21/21
  meet-stage: 0/21
  googlechat: 0/21
  google-apps-script-web: 21/21
  email: 0/21
  pdf: 0/21
maturity: stable
source: atoms/schema.yaml
---

# Code & Technical Reference

> 21 atoms · `*` = degraded (limited support) · Bold surface = full support

| Atom type | Description | Surfaces | Key fields |
|-----------|-------------|----------|------------|
| `code` | syntax-highlighted fenced code block | **Web/Blog** · **GAS Web App** · **PDF** | `language` — string<br>`content` — string |
| `annotated_code` | code block with numbered callout bubbles on specific lines explanation list below | **Web/Blog** · **GAS Web App** | `language` — string<br>`code` — string<br>`caption` — string (optional)<br>`annotations` |
| `code_diff` | server-side unified diff view with green additions and red removals | **Web/Blog** · **GAS Web App** | `old_code` — string. The original text (before state).<br>`new_code` — string. The updated text (after state).<br>`label` — string (optional). Title shown in the header bar.<br>`language` — string (optional). Language badge shown in header, e.g. "python", "typescript".<br>`show_line_numbers` — bool (optional). Show line numbers. Default true.<br>`context_lines` — integer (optional). Unchanged lines shown around each change. Default 3. |
| `code_snippet_pair` | two code blocks side by side without diff highlighting diff highlighting. | **Web/Blog** · **GAS Web App** | `left_code` — string<br>`right_code` — string<br>`language` — string<br>`left_label` — string<br>`right_label` — string |
| `tabbed_code` | organize multiple programming language snippets inside an interactive tab container | **Web/Blog** · **GAS Web App** | `tabs` — array. Collection of objects containing the language identifier, tab label, and code string. |
| `terminal_block` | display terminal commands and code output in a simulated console window | **Web/Blog** · **GAS Web App** | `command` — string. The execution command displayed at the prompt.<br>`output` — string. The stdout or stderr text block response from the command.<br>`shell` — string: bash | zsh | powershell | cmd. The console design theme. |
| `file_tree` | present hierarchical directory structures and files for software project navigation | **Web/Blog** · **GAS Web App** | `nodes` — array. Highly structured list of folder and file objects with nesting indicators. |
| `http_request_block` | document REST API endpoints with HTTP methods, headers, and payloads | **Web/Blog** · **GAS Web App** | `method` — string: GET | POST | PUT | DELETE | PATCH. The HTTP verb.<br>`url` — string. The fully qualified or relative API endpoint route.<br>`headers` — object. Key-value pairs detailing required HTTP headers.<br>`body` — string. Optional request payload, typically stringified JSON. |
| `env_var_list` | list configuration environment variables with descriptions and default values | **Web/Blog** · **GAS Web App** | `variables` — array. List of objects including key name, description, requirement status, and default. |
| `api_reference` | API endpoint method parameters and response docs returns, example | **Web/Blog** · **GAS Web App** · **PDF** | `name` — string<br>`kind` — function | endpoint | class | method<br>`method` — string (optional)<br>`description` — string<br>`deprecated` — bool (optional)<br>`parameters`<br>`returns` — string (optional)<br>`example` —  |
| `api_param_table` | reference table detailing API parameters, data types, and default values | **Web/Blog** · **GAS Web App** | `parameters` — array. Objects defining name, type, required flag, default value, and description. |
| `keyboard_shortcut` | display visual keyboard key combinations for application shortcuts and hotkeys | **Web/Blog** · **GAS Web App** | `keys` — array. Individual key characters like Ctrl, Shift, or C to join.<br>`action` — string. The function or command triggered by the keystroke combination. |
| `cli_command` | copyable single-line terminal command execution string | **Web/Blog** · **GAS Web App** | `command` — string. The exact shell command to be copied and executed. |
| `log_output` | scrollable monospace server or compiler log output block | **Web/Blog** · **GAS Web App** | `logs` — string. The raw console log output text block. |
| `json_tree_viewer` | expandable visual explorer for nested JSON data | **Web/Blog** · **GAS Web App** | `data` — string. The raw valid JSON string to parse and render. |
| `version_badge` | software release or dependency version number tag | **Web/Blog** · **GAS Web App** | `version` — string. The semantic version number or release label to display.<br>`status` — string: stable | beta | alpha | rc. The lifecycle stage. |
| `deprecation_notice` | warning banner for deprecated features or unsupported APIs | **Web/Blog** · **GAS Web App** | `alternative` — string. Recommended migration path or replacement feature.<br>`removal_version` — string. Optional version when the feature will be removed. |
| `experimental_banner` | highlight experimental or unstable feature notice callout | **Web/Blog** · **GAS Web App** | `message` — string. Context or feedback links for the unstable feature. |
| `copy_to_clipboard` | copy-to-clipboard button with inline code and feedback | **Web/Blog** · **GAS Web App** | `text` — string. Display label.<br>`value` — string. Value copied to clipboard. |
| `framed_screenshot` | device-framed screenshot with optional caption browser, phone). | **Web/Blog** · **GAS Web App** | `image_url` — string<br>`alt_text` — string<br>`device_type` — string<br>`caption` — string |
| `copy_code_button` | button to copy specified text or code to clipboard | **Web/Blog** · **GAS Web App** | `text_to_copy` — string. The raw string content sent to clipboard when clicked. |
