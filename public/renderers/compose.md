# Compose renderer support

Compose atoms are our own native Compose components (about 500 registered custom components, built by us on top of a2ui-kmp), plus atoms whose root is a Basic component (Text, Column, Button, Tabs and so on) drawn by the Basic catalog. Native means the lane case rendered without error with the atom's own type present, measured on Compose Desktop; it does not mean visual parity with the web painter. An on-device Android run is only partial (2 of 42 test payloads captured), so no device claim is made.

- Package: a2ui-kmp
- Version measured: a2ui-kmp 1.0.0-alpha02 (third-party Kotlin Multiplatform rebuild of androidx.a2ui 1.0.0-alpha02; spec v0.9.1 only)
- Protocol: v0.9 only (spec v0.9.1; no v1.0 claim)
- Platform: Compose Desktop on the JVM (Jetpack Compose family); not Android
- Measured: 2026-11-13

## Coverage of the 573 public atoms

- Native: 533
- Not supported: 37
- Not measured: 3

## Not supported (37)

- `agent_sketchpad`: component type unknown to the renderer
- `brick_build_3d`: component type unknown to the renderer
- `canvas_plexus`: component type unknown to the renderer
- `content_tabs`: component type unknown to the renderer
- `cursor_glow`: component type unknown to the renderer
- `cursor_trail`: component type unknown to the renderer
- `embed_codepen`: component type unknown to the renderer
- `embed_gist`: component type unknown to the renderer
- `embed_google_slides`: component type unknown to the renderer
- `embed_stackblitz`: component type unknown to the renderer
- `figma_embed`: component type unknown to the renderer
- `geo_contour_waves`: component type unknown to the renderer
- `geo_europe_airspace`: component type unknown to the renderer
- `geo_iso_fleet`: component type unknown to the renderer
- `geo_iso_heli_hover`: component type unknown to the renderer
- `geo_iso_rocket_launch`: component type unknown to the renderer
- `geo_iso_takeoff`: component type unknown to the renderer
- `geo_mercator_radar`: component type unknown to the renderer
- `globe_3d`: component type unknown to the renderer
- `isometric_mesh`: component type unknown to the renderer
- `lens_grid`: component type unknown to the renderer
- `live_demo_embed`: component type unknown to the renderer
- `lottie_animation`: component type unknown to the renderer
- `magnetic_element`: component type unknown to the renderer
- `maps_embed`: component type unknown to the renderer
- `me`: component type unknown to the renderer
- `media_stream_card`: component type unknown to the renderer
- `motion_bricks`: component type unknown to the renderer
- `motion_shader`: component type unknown to the renderer
- `particle_burst`: component type unknown to the renderer
- `preview_frame`: component type unknown to the renderer
- `progress_store`: component type unknown to the renderer
- `scroll_trigger`: component type unknown to the renderer
- `spotlight_cursor`: component type unknown to the renderer
- `spring_nodes`: component type unknown to the renderer
- `video_checkpoint`: component type unknown to the renderer
- `video_pair`: component type unknown to the renderer

## Not measured (3)

`choropleth_map`, `geo_map`, `motion_map3d`

Overview: https://a2uicatalog.ai/renderers/

Independent and unofficial; not affiliated with Google, CopilotKit or the Vue project. React, Angular, Lit, CopilotKit, Vue and their logos are trademarks or registered trademarks of their respective owners. They are used here only to identify the renderers this catalog has been tested with, and do not imply affiliation with or endorsement by those owners. Logo artwork: simple-icons (CC0) for React, Lit, Angular and Vue, and CopilotKit's public repository for its mark; the marks remain their owners'. Flutter and Compose are likewise trademarks of their respective owners; no logo is shown for them.
