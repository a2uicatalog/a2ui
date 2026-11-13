# Flutter renderer support

Partial coverage: only a part of the atoms are ported to native Flutter widgets. Text parity with the web painter was checked on the atoms listed in the parity sweep; the Basic lane was not measured by us; no device run. Measured on a private, unpublished build, after the lane merges.

- Package: a2ui_flutter
- Version measured: a2ui_flutter 0.3.0 (a2ui_core 0.7.0), private build
- Protocol: v1.0
- Platform: Flutter widget-test engine (headless); no device
- Measured: 2026-11-13

## Coverage of the 573 public atoms

- Native: 450
- Degraded: 30
- Not supported: 69
- Not measured: 24

## Degraded (30)

- `audio_player`: lowered to Basic components
- `body`: lowered to Basic components
- `bullet_list`: lowered to Basic components
- `color_section`: lowered to Basic components
- `columns`: lowered to Basic components
- `cta_button`: lowered to Basic components
- `divider`: lowered to Basic components
- `form`: lowered to Basic components
- `glass_card`: lowered to Basic components
- `google_icon`: lowered to Basic components
- `heading`: lowered to Basic components
- `hub`: lowered to Basic components
- `image`: lowered to Basic components
- `info_card`: lowered to Basic components
- `link_button`: lowered to Basic components
- `markdown_block`: lowered to Basic components
- `modal`: lowered to Basic components
- `motion_envelope`: lowered to Basic components
- `motion_group`: lowered to Basic components
- `motion_layer`: lowered to Basic components
- `motion_mask`: lowered to Basic components
- `numbered_list`: lowered to Basic components
- `paragraph`: lowered to Basic components
- `quote`: lowered to Basic components
- `split_pane`: lowered to Basic components
- `subheading`: lowered to Basic components
- `tabs`: lowered to Basic components
- `text_block`: lowered to Basic components
- `video_card`: lowered to Basic components
- `youtube`: lowered to Basic components

## Not supported (69)

- `agent_sketchpad`: component type unknown to the renderer
- `animated_counter`: component type unknown to the renderer
- `brevet_timeline`: component type unknown to the renderer
- `brick_build_3d`: component type unknown to the renderer
- `canvas_plexus`: component type unknown to the renderer
- `confetti_burst`: component type unknown to the renderer
- `content_tabs`: a nested atom type is unknown
- `copy_prompt`: component type unknown to the renderer
- `count_up_stat`: component type unknown to the renderer
- `countdown_ring`: component type unknown to the renderer
- `cursor_glow`: component type unknown to the renderer
- `cursor_trail`: component type unknown to the renderer
- `deadline_ticker`: component type unknown to the renderer
- `domain_picker`: component type unknown to the renderer
- `embed_codepen`: component type unknown to the renderer
- `embed_gist`: component type unknown to the renderer
- `embed_google_slides`: component type unknown to the renderer
- `embed_stackblitz`: component type unknown to the renderer
- `expandable_list`: component type unknown to the renderer
- `feed_status`: component type unknown to the renderer
- `figma_embed`: component type unknown to the renderer
- `filterable_list`: component type unknown to the renderer
- `flashcard_deck`: component type unknown to the renderer
- `geo_contour_waves`: component type unknown to the renderer
- `geo_europe_airspace`: component type unknown to the renderer
- `geo_iso_fleet`: component type unknown to the renderer
- `geo_iso_heli_hover`: component type unknown to the renderer
- `geo_iso_rocket_launch`: component type unknown to the renderer
- `geo_iso_takeoff`: component type unknown to the renderer
- `geo_mercator_radar`: component type unknown to the renderer
- `globe_3d`: component type unknown to the renderer
- `isometric_mesh`: component type unknown to the renderer
- `knowledge_check`: component type unknown to the renderer
- `lens_grid`: component type unknown to the renderer
- `live_clock`: component type unknown to the renderer
- `live_demo_embed`: component type unknown to the renderer
- `live_metric`: component type unknown to the renderer
- `lottie_animation`: component type unknown to the renderer
- `magnetic_element`: component type unknown to the renderer
- `maps_embed`: component type unknown to the renderer
- `me`: component type unknown to the renderer
- `media_stream_card`: component type unknown to the renderer
- `motion_bricks`: component type unknown to the renderer
- `motion_shader`: component type unknown to the renderer
- `particle_burst`: component type unknown to the renderer
- `preview_frame`: component type unknown to the renderer
- `progress_reveal`: component type unknown to the renderer
- `progress_store`: component type unknown to the renderer
- `reading_progress_bar`: component type unknown to the renderer
- `reveal_on_scroll`: component type unknown to the renderer
- `scenario_branch`: component type unknown to the renderer
- `scramble_reveal`: component type unknown to the renderer
- `scroll_progress`: component type unknown to the renderer
- `scroll_trigger`: component type unknown to the renderer
- `speed_counter`: component type unknown to the renderer
- `spotlight_card`: component type unknown to the renderer
- `spotlight_cursor`: component type unknown to the renderer
- `spring_nodes`: component type unknown to the renderer
- `stance`: component type unknown to the renderer
- `study_timer`: component type unknown to the renderer
- `tab_group`: component type unknown to the renderer
- `terminal_boot`: component type unknown to the renderer
- `theme_toggle`: component type unknown to the renderer
- `tilt_card`: component type unknown to the renderer
- `treemap`: component type unknown to the renderer
- `typewriter`: component type unknown to the renderer
- `user_greeting`: component type unknown to the renderer
- `video_checkpoint`: component type unknown to the renderer
- `video_pair`: component type unknown to the renderer

## Not measured (24)

`arc_diagram`, `block_robot`, `block_rocket`, `box_plot`, `candlestick_chart`, `chord_diagram`, `choropleth_map`, `circle_pack`, `contour_plot`, `geo_map`, `histogram`, `histogram2d`, `module_map`, `motion_map3d`, `motion_transition`, `parallel_coords`, `playbook`, `polar_chart`, `quiver`, `scatter_matrix`, `sunburst`, `ternary_plot`, `voronoi`, `waterfall`

Overview: https://a2uicatalog.ai/renderers/

Independent and unofficial; not affiliated with Google, CopilotKit or the Vue project. React, Angular, Lit, CopilotKit, Vue and their logos are trademarks or registered trademarks of their respective owners. They are used here only to identify the renderers this catalog has been tested with, and do not imply affiliation with or endorsement by those owners. Logo artwork: simple-icons (CC0) for React, Lit, Angular and Vue, and CopilotKit's public repository for its mark; the marks remain their owners'. Flutter and Compose are likewise trademarks of their respective owners; no logo is shown for them.
