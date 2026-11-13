# CopilotKit renderer support

CopilotKit draws our atoms inside ITS wrapper and theme, so the custom-lane numbers measure whether the wrapper changes how our atoms look and behave, not CopilotKit's own components. Primary measurement: version 1.87.0 on A2UI 1.0, our custom lane and four pixel lanes; the behaviour lane was not run for 1.87.0, so behaviour is recorded as not run, never as a pass.

- Package: @copilotkit/a2ui-renderer
- Version measured: @copilotkit/a2ui-renderer 1.87.0 (A2UI 1.0, web_core 0.15.0)
- Protocol: v1.0 (A2UI 1.0 catalog path)
- Platform: web (React, stock CopilotKit renderer, Chromium)
- Measured: 2026-11-13

## Coverage of the 573 public atoms

- Drawn: 482
- Drawn with differences: 35
- Not verified: 34
- Not supported: 0
- Not measured: 22

## Drawn with differences (35)

- `ai_build_trace`: pixels differ from React (light 480)
- `audio_player`: contrast worse than React (dark 360); contrast worse than React (dark 480); overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React
- `body`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React
- `bullet_list`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React
- `code_snippet_pair`: pixels differ from React (dark 480); pixels differ from React (light 480)
- `color_section`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React
- `columns`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `content_tabs`: overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `cta_button`: contrast worse than React (dark 360); contrast worse than React (dark 480); pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `divider`: no visible text in the example; overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `gemini_prompt`: pixels differ from React (light 360)
- `glass_card`: contrast worse than React (dark 360); contrast worse than React (dark 480); overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `google_icon`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `heading`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `hub`: overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `image`: overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `image_with_caption`: pixels differ from React (dark 480); pixels differ from React (light 480)
- `info_card`: contrast worse than React (dark 360); contrast worse than React (dark 480); overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `link_button`: contrast worse than React (dark 360); contrast worse than React (dark 480); pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `markdown_block`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `modal`: contrast worse than React (dark 360); contrast worse than React (dark 480); pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `motion_envelope`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `motion_group`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `motion_layer`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `motion_mask`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `numbered_list`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React
- `page_header`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `paragraph`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `quote`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React
- `split_pane`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `subheading`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `tabs`: overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `text_block`: pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)
- `video_card`: overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React
- `youtube`: contrast worse than React (dark 360); contrast worse than React (dark 480); overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480)

## Not verified (34)

- `adsb_feed`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `canvas_plexus`: no visible text in the example
- `cursor_glow`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `cursor_trail`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `dark_divider`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `floating_orbs`: no visible text in the example
- `gdm_rocket_panel`: no visible text in the example
- `incident_log`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `isometric_mesh`: no visible text in the example
- `loading_skeleton`: no visible text in the example
- `lottie_animation`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `maps_embed`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `me`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `media_stream_card`: no visible text in the example
- `metar_feed`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `motion_bricks`: blank on both sides (light 360); blank on both sides (light 480); no visible text in the example
- `motion_finish`: blank on both sides (light 360); blank on both sides (light 480)
- `motion_rays`: no visible text in the example
- `motion_shader`: no visible text in the example
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
