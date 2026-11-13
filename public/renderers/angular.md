# Angular renderer support

Measured against the React lane on the same code.

- Package: @a2ui/angular
- Version measured: @a2ui/angular 0.14.0 (web_core 0.15.0)
- Protocol: v0.9
- Platform: web (Angular, Chromium)
- Measured: 2026-11-13

## Coverage of the 573 public atoms

- Drawn: 517
- Drawn with differences: 3
- Not verified: 31
- Not supported: 0
- Not measured: 22

## Drawn with differences (3)

- `icon_badge`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `icon_row`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `image`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)

## Not verified (31)

- `adsb_feed`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `cursor_glow`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `cursor_trail`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `dark_divider`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `divider`: no visible text in the example
- `floating_orbs`: no visible text in the example
- `incident_log`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `loading_skeleton`: no visible text in the example
- `lottie_animation`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `maps_embed`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `me`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `media_stream_card`: no visible text in the example
- `metar_feed`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `motion_bricks`: blank on both sides (light 360); blank on both sides (light 480)
- `motion_finish`: blank on both sides (light 360); blank on both sides (light 480)
- `motion_rays`: no visible text in the example
- `motion_shape`: no visible text in the example
- `motion_video`: no visible text in the example
- `palette`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `particle_burst`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `progress_store`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `scroll_progress`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `service_status_board`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `shortcut_legend`: no visible text in the example
- `skeleton`: no visible text in the example
- `skeleton_stage_card`: no visible text in the example
- `spacer`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `spotlight_cursor`: no visible text in the example
- `stat_pulse`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `weather_now`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `weather_outlook`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example

## Not measured (22)

`arc_diagram`, `block_robot`, `block_rocket`, `box_plot`, `candlestick_chart`, `chord_diagram`, `choropleth_map`, `circle_pack`, `contour_plot`, `geo_map`, `histogram`, `histogram2d`, `motion_map3d`, `motion_transition`, `parallel_coords`, `polar_chart`, `quiver`, `scatter_matrix`, `sunburst`, `ternary_plot`, `voronoi`, `waterfall`

Overview: https://a2uicatalog.ai/renderers/

Independent and unofficial; not affiliated with Google, CopilotKit or the Vue project. React, Angular, Lit, CopilotKit, Vue and their logos are trademarks or registered trademarks of their respective owners. They are used here only to identify the renderers this catalog has been tested with, and do not imply affiliation with or endorsement by those owners. Logo artwork: simple-icons (CC0) for React, Lit, Angular and Vue, and CopilotKit's public repository for its mark; the marks remain their owners'. Flutter and Compose are likewise trademarks of their respective owners; no logo is shown for them.
