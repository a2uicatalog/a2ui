# Which renderer draws which atom

Every atom says where it appears (`x-surfaces`); `x-renderers` says what draws it, measured per renderer. 573 public atoms, 7 renderers, 7 of them measured.

| Renderer | Package | Version measured | Statuses |
|---|---|---|---|
| [React](https://a2uicatalog.ai/renderers/react/) | @a2ui/react | @a2ui/react 0.15.0 (web_core 0.15.0) | Drawn 517, Not verified 34, Not measured 22 |
| [Lit](https://a2uicatalog.ai/renderers/lit/) | @a2ui/lit | @a2ui/lit 0.15.0 (web_core 0.15.0) | Drawn 518, Drawn with differences 2, Not verified 31, Not measured 22 |
| [Angular](https://a2uicatalog.ai/renderers/angular/) | @a2ui/angular | @a2ui/angular 0.14.0 (web_core 0.15.0) | Drawn 517, Drawn with differences 3, Not verified 31, Not measured 22 |
| [CopilotKit](https://a2uicatalog.ai/renderers/copilotkit/) | @copilotkit/a2ui-renderer | @copilotkit/a2ui-renderer 1.87.0 (A2UI 1.0, web_core 0.15.0) | Drawn 482, Drawn with differences 35, Not verified 34, Not measured 22 |
| [a2ui-vue](https://a2uicatalog.ai/renderers/a2ui-vue/) | a2ui-vue | a2ui-vue 0.9.5 (Vue 3.5.13, web_core 0.9.1) | Drawn 482, Drawn with differences 35, Not verified 34, Not measured 22 |
| [Flutter](https://a2uicatalog.ai/renderers/flutter/) | a2ui_flutter | a2ui_flutter 0.3.0 (a2ui_core 0.7.0), private build | Native 450, Degraded 30, Not supported 69, Not measured 24 |
| [Compose](https://a2uicatalog.ai/renderers/compose/) | a2ui-kmp | a2ui-kmp 1.0.0-alpha02 (third-party Kotlin Multiplatform rebuild of androidx.a2ui 1.0.0-alpha02; spec v0.9.1 only) | Native 28, Not supported 523, Not measured 22 |

Data: https://a2uicatalog.ai/catalogue/renderer-matrix-v1.json; per atom in `x-renderers` of https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json and https://a2uicatalog.ai/spec.json.

Independent and unofficial; not affiliated with Google, CopilotKit or the Vue project. React, Angular, Lit, CopilotKit, Vue and their logos are trademarks or registered trademarks of their respective owners. They are used here only to identify the renderers this catalog has been tested with, and do not imply affiliation with or endorsement by those owners. Logo artwork: simple-icons (CC0) for React, Lit, Angular and Vue, and CopilotKit's public repository for its mark; the marks remain their owners'. Flutter and Compose are likewise trademarks of their respective owners; no logo is shown for them.
