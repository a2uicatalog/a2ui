# React renderer support

The reference renderer: the other web renderers are compared with it pixel for pixel. Its own pixel column is measured against its own frozen reference shots, so parity is recorded as reference, not as a pass.

- Package: @a2ui/react
- Version measured: @a2ui/react 0.15.0 (web_core 0.15.0)
- Protocol: v1.0 through the web_core v1_0 module (the Basic lane of the gate runs v0.9)
- Platform: web (React, Chromium)
- Measured: 2026-11-13

## Coverage of the 573 public atoms

- Drawn: 517
- Drawn with differences: 0
- Not verified: 34
- Not supported: 0
- Not measured: 22

## Not verified (34)

- `adsb_feed`: no visible text in the example
- `canvas_plexus`: no visible text in the example
- `cursor_glow`: no visible text in the example
- `cursor_trail`: no visible text in the example
- `dark_divider`: no visible text in the example
- `divider`: no visible text in the example
- `floating_orbs`: no visible text in the example
- `gdm_rocket_panel`: no visible text in the example
- `incident_log`: no visible text in the example
- `isometric_mesh`: no visible text in the example
- `loading_skeleton`: no visible text in the example
- `lottie_animation`: no visible text in the example
- `maps_embed`: no visible text in the example
- `me`: no visible text in the example
- `media_stream_card`: no visible text in the example
- `metar_feed`: no visible text in the example
- `motion_bricks`: no visible text in the example
- `motion_rays`: no visible text in the example
- `motion_shader`: no visible text in the example
- `motion_shape`: no visible text in the example
- `motion_video`: no visible text in the example
- `palette`: no visible text in the example
- `particle_burst`: no visible text in the example
- `progress_store`: no visible text in the example
- `scroll_progress`: no visible text in the example
- `service_status_board`: no visible text in the example
- `shortcut_legend`: no visible text in the example
- `skeleton`: no visible text in the example
- `skeleton_stage_card`: no visible text in the example
- `spacer`: no visible text in the example
- `spotlight_cursor`: no visible text in the example
- `stat_pulse`: no visible text in the example
- `weather_now`: no visible text in the example
- `weather_outlook`: no visible text in the example

## Not measured (22)

`arc_diagram`, `block_robot`, `block_rocket`, `box_plot`, `candlestick_chart`, `chord_diagram`, `choropleth_map`, `circle_pack`, `contour_plot`, `geo_map`, `histogram`, `histogram2d`, `motion_map3d`, `motion_transition`, `parallel_coords`, `polar_chart`, `quiver`, `scatter_matrix`, `sunburst`, `ternary_plot`, `voronoi`, `waterfall`

Overview: https://a2uicatalog.ai/renderers/

Independent and unofficial; not affiliated with Google, CopilotKit or the Vue project. React, Angular, Lit, CopilotKit, Vue and their logos are trademarks or registered trademarks of their respective owners. They are used here only to identify the renderers this catalog has been tested with, and do not imply affiliation with or endorsement by those owners. Logo artwork: simple-icons (CC0) for React, Lit, Angular and Vue, and CopilotKit's public repository for its mark; the marks remain their owners'. Flutter and Compose are likewise trademarks of their respective owners; no logo is shown for them.
