# TypeScript / frontend rules

LockLearn frontend is TypeScript + Lit + Vite.

- keep strict TypeScript enabled;
- prefer small Web Components and typed data contracts;
- frontend never owns authorization decisions;
- all application mutations go through Home Assistant WebSocket commands;
- no runtime CDN dependencies;
- never render dataset-provided raw HTML or use `unsafeHTML` for third-party data;
- preserve keyboard/accessibility/mobile behavior;
- use `lang` metadata for learned-language content, especially CJK;
- treat HA frontend internals as unstable implementation details and isolate them.
