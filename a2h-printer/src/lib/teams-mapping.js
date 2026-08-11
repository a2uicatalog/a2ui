// src/lib/teams-mapping.js — ported from slack-compiler/teams-mapping.js
// (AUTO-GENERATED there by gen_teams_mapping.py from teams-mapping.json).
// Runtime lookup for the Teams Adaptive Cards compiler (teams-blocks.js):
// which atoms compile to a real Adaptive Card element, and which
// target/bucket each needs. Mirrors slack-mapping.js's role exactly.
//
// Deliberately does NOT port TEAMS_CHART_ELEMENTS from the source file —
// that table predates teams-blocks.js's own documented correction #1
// ("CHARTS ARE IMAGES, NOT ELEMENTS"): every chart atom below already
// carries target:"Image", bucket:"D", which is what actually drives
// compileAtom's dispatch. TEAMS_CHART_ELEMENTS mapped chart atoms to
// Chart.* element names teams-blocks.js has no emitter for at all (no
// eChart exists) — using it would silently degrade every chart to a plain
// TextBlock instead of the intended pre-rendered image.
export const TEAMS_MAPPING = {
  "accordion_item": {
    "bucket": "A",
    "target": "Action.ShowCard"
  },
  "alert_banner": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "callout": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "collapsible_panel": {
    "bucket": "A",
    "target": "Action.ToggleVisibility"
  },
  "columns": {
    "bucket": "A",
    "target": "ColumnSet"
  },
  "combobox": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "content_tabs": {
    "bucket": "A",
    "target": "Action.ToggleVisibility"
  },
  "cta_button": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "data_table_sortable": {
    "bucket": "A",
    "target": "Table"
  },
  "divider": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "domain_picker": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "file_upload": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_checkbox_group": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_date_picker": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_field": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_input": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_radio_group": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_select": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_slider": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_switch_group": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "form_textarea": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "heading": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "image": {
    "bucket": "A",
    "target": "Image"
  },
  "image_with_caption": {
    "bucket": "A",
    "target": "Image"
  },
  "inline_alert": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "key_value": {
    "bucket": "A",
    "target": "Table"
  },
  "link_button": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "metric_row": {
    "bucket": "A",
    "target": "Table"
  },
  "modal": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "module_map": {
    "bucket": "A",
    "target": "Table"
  },
  "multi_select_input": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "nav_link": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "numbered_list": {
    "bucket": "A",
    "target": "Table"
  },
  "otp_input": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "page_header": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "section_break": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "sheet_form_submit": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "spacer": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "split_pane": {
    "bucket": "A",
    "target": "ColumnSet"
  },
  "stat_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "step_progress": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "stepper": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "steps": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "summary_box": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "table": {
    "bucket": "A",
    "target": "Table"
  },
  "text_callout": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "toggle_switch": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "match_schedule": {
    "bucket": "A",
    "target": "Table"
  },
  "standings_table": {
    "bucket": "A",
    "target": "Table"
  },
  "action_required_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "bento_grid": {
    "bucket": "A",
    "target": "ColumnSet"
  },
  "carousel": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "caution_block": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "choicebox_group": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "color_swatch_grid": {
    "bucket": "A",
    "target": "Table"
  },
  "counter_group": {
    "bucket": "A",
    "target": "Table"
  },
  "custom_checkbox_group": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "dark_divider": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "data_grid": {
    "bucket": "A",
    "target": "Table"
  },
  "expandable_list": {
    "bucket": "A",
    "target": "Container"
  },
  "faq_accordion": {
    "bucket": "A",
    "target": "Action.ShowCard"
  },
  "gallery": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "glass_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "icon_checklist": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "icon_stat_row": {
    "bucket": "A",
    "target": "Table"
  },
  "image_pair": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "metric_comparison_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "metric_delta": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "next_step_strip": {
    "bucket": "A",
    "target": "Table"
  },
  "person_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "pipeline": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "pull_stat": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "resources_list": {
    "bucket": "A",
    "target": "Table"
  },
  "section_label": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "side_by_side_spec": {
    "bucket": "A",
    "target": "Table"
  },
  "split_stat": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "status_timeline": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "take_away_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "task_list": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "two_tone_card": {
    "bucket": "A",
    "target": "Container"
  },
  "variant_selector": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "video_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "video_pair": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "video_thumbnail": {
    "bucket": "A",
    "target": "Image"
  },
  "zoomable_image": {
    "bucket": "A",
    "target": "Image"
  },
  "author_bio_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "headline_list": {
    "bucket": "A",
    "target": "Table"
  },
  "news_digest": {
    "bucket": "A",
    "target": "Table"
  },
  "related_posts_grid": {
    "bucket": "A",
    "target": "Table"
  },
  "search_result_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "series_overview_card": {
    "bucket": "A",
    "target": "Table"
  },
  "source_citation": {
    "bucket": "A",
    "target": "Table"
  },
  "table_of_contents": {
    "bucket": "A",
    "target": "Table"
  },
  "tooltip_glossary": {
    "bucket": "A",
    "target": "Table"
  },
  "brevet_automatismes": {
    "bucket": "A",
    "target": "Table"
  },
  "brevet_timeline": {
    "bucket": "A",
    "target": "Table"
  },
  "capability_checklist": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "certification_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "checklist_interactive": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "cohort_progress_board": {
    "bucket": "A",
    "target": "Table"
  },
  "course_progress_card": {
    "bucket": "A",
    "target": "Table"
  },
  "flashcard_deck": {
    "bucket": "A",
    "target": "Table"
  },
  "learning_objectives": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "learning_path_selector": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "match_exercise": {
    "bucket": "A",
    "target": "Table"
  },
  "onboarding_stepper": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "prerequisite_checklist": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "reflection_prompt": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "rubric_card": {
    "bucket": "A",
    "target": "Table"
  },
  "article_hero": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "case_study_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "comparison_grid": {
    "bucket": "A",
    "target": "ColumnSet"
  },
  "cta_section": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "dark_hero": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "expert_endorsement": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "feature_matrix": {
    "bucket": "A",
    "target": "ColumnSet"
  },
  "follow_button": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "follow_cta": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "follow_up_chips": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "github_repo_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "gradient_hero": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "linkedin_post_image": {
    "bucket": "A",
    "target": "Image"
  },
  "media_mention_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "newsletter_cta": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "pricing_tier_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "pricing_tier_group": {
    "bucket": "A",
    "target": "Table"
  },
  "rating_summary_bar": {
    "bucket": "A",
    "target": "Table"
  },
  "review_callout": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "star_rating_input": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "testimonial_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "catalogue_provenance": {
    "bucket": "A",
    "target": "Table"
  },
  "domain_brief": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "llm_comparison_table": {
    "bucket": "A",
    "target": "Table"
  },
  "model_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "multi_surface": {
    "bucket": "A",
    "target": "Table"
  },
  "renderer_stats": {
    "bucket": "A",
    "target": "Table"
  },
  "token_budget_meter": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "api_param_table": {
    "bucket": "A",
    "target": "Table"
  },
  "breaking_banner": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "changelog_entry": {
    "bucket": "A",
    "target": "Table"
  },
  "deprecation_notice": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "entity_list": {
    "bucket": "A",
    "target": "Table"
  },
  "env_var_list": {
    "bucket": "A",
    "target": "Table"
  },
  "experimental_banner": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "inventory_table": {
    "bucket": "A",
    "target": "Table"
  },
  "jira_ticket": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "leaderboard_card": {
    "bucket": "A",
    "target": "Table"
  },
  "live_aggregator": {
    "bucket": "A",
    "target": "Table"
  },
  "notification_stack": {
    "bucket": "A",
    "target": "Table"
  },
  "order_status_card": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "poll_block": {
    "bucket": "A",
    "target": "Table"
  },
  "product_spec_table": {
    "bucket": "A",
    "target": "Table"
  },
  "product_thumbnail": {
    "bucket": "A",
    "target": "Image"
  },
  "shortcut_legend": {
    "bucket": "A",
    "target": "Table"
  },
  "sprint_board": {
    "bucket": "A",
    "target": "TextBlock"
  },
  "status_dashboard": {
    "bucket": "A",
    "target": "Table"
  },
  "vote_button_group": {
    "bucket": "A",
    "target": "ActionSet"
  },
  "back_button": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "badge": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "badge_group": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "blockquote": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "body": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "bullet_list": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "chip_group": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "code": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "code_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "code_diff": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "diagram": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "empty_state": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "file_tree": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "google_icon": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "highlight_box": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "hub": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "icon_list": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "info_card": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "inline_code": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "json_tree_viewer": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "key_takeaways": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_grid": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "markdown_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "paragraph": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "progress_bar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "progress_ring": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "quiet_link": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "quote": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "script_run_button": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "status_pill": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "subheading": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "tabbed_code": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "tag_chip": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "text_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "timeline": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "tool_tile": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "tree_view": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "annotated_code": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "annotation_highlight": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "audio_link": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "audio_player": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "avatar_group": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "before_after": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "before_after_stack": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "code_snippet_pair": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "copy_code_button": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "decision_tree": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "document_link": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "expandable_text": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "feedback_prompt": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "highlighted_text": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "icon_badge": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "icon_row": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "inline_feedback_message": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lozenge": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "math_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "pdf_preview": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "progress_circle": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "reaction_group": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "repo_links": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "sidebar_note": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "tag_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "tag_cloud": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "text_analysis": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "text_highlight": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "version_badge": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "abbr_tooltip": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "anchor_list": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "article_series_nav": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "closing": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "concept_ladder": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "concept_rung": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "display_quote": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "footnote": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "footnote_group": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "further_reading": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "glossary_inline": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "glossary_term": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "intro": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "post_metadata_bar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "reading_progress_bar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "share_quote": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "social_share_bar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "time_estimate": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "embed_codepen": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "embed_gist": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "embed_google_slides": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "embed_stackblitz": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "embed_tweet": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "figma_embed": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "framed_screenshot": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "live_demo_embed": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lottie_animation": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "maps_embed": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "media_stream_card": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "social_feed_embed": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "youtube": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "scroll_gallery": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "achievement_badge": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "cert_disclaimer": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "completion_gate": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "difficulty_badge": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "fill_in_blank": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "knowledge_check": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lesson_nav": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "progress_checkpoint": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "quiz_question": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "quiz_result_summary": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "quiz_set": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "scenario_branch": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "scenario_case": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "score_summary": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "spaced_repetition_card": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "study_timer": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "video_checkpoint": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "xp_bar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_context": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_similar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_quotes": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_structure": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_eli5": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_freeform": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_synthesis": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "lens_themes": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "blockquote_with_avatar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "contributor_list": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "customer_logo_grid": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "dark_feature_grid": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "feature_grid": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "icon_feature_grid": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "pros_cons_list": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "rating_comparison": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "rating_stars": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "social_proof_banner": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "star_rating_display": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "versus_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "ai_build_trace": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "atom_anatomy": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "copy_prompt": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "gemini_handoff": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "gemini_prompt": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "live_edit": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "prompt_template": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "prompt_to_schema": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "api_reference": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "cli_command": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "command_step": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "countdown_ring": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "countdown_timer": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "deadline_ticker": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "feed_status": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "http_request_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "keyboard_shortcut": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "live_clock": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "live_metric": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "live_vote": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "log_output": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "notification_badge": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "presence_bar": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "raise_hand": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "release_notes": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "risk_flag": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "roadmap_card": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "sla_timer_display": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "terminal_block": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "toast_notification": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "playbook": {
    "bucket": "B",
    "target": "TextBlock"
  },
  "breadcrumb": {
    "bucket": "D",
    "target": "Image"
  },
  "color_section": {
    "bucket": "D",
    "target": "Image"
  },
  "copy_to_clipboard": {
    "bucket": "D",
    "target": "Image"
  },
  "data_source": {
    "bucket": "D",
    "target": "Image"
  },
  "firestore_read": {
    "bucket": "D",
    "target": "Image"
  },
  "nav_bar": {
    "bucket": "D",
    "target": "Image"
  },
  "pagination": {
    "bucket": "D",
    "target": "Image"
  },
  "palette": {
    "bucket": "D",
    "target": "Image"
  },
  "print_button": {
    "bucket": "D",
    "target": "Image"
  },
  "progress_store": {
    "bucket": "D",
    "target": "Image"
  },
  "segmented_control": {
    "bucket": "D",
    "target": "Image"
  },
  "sheet_preview": {
    "bucket": "D",
    "target": "Image"
  },
  "skeleton": {
    "bucket": "D",
    "target": "Image"
  },
  "spinner": {
    "bucket": "D",
    "target": "Image"
  },
  "tab_bar": {
    "bucket": "D",
    "target": "Image"
  },
  "tabs": {
    "bucket": "D",
    "target": "Image"
  },
  "tooltip": {
    "bucket": "D",
    "target": "Image"
  },
  "adsb_feed": {
    "bucket": "D",
    "target": "Image"
  },
  "airspace_command_deck": {
    "bucket": "D",
    "target": "Image"
  },
  "canvas_plexus": {
    "bucket": "D",
    "target": "Image"
  },
  "geo_contour_waves": {
    "bucket": "D",
    "target": "Image"
  },
  "geo_europe_airspace": {
    "bucket": "D",
    "target": "Image"
  },
  "geo_iso_fleet": {
    "bucket": "D",
    "target": "Image"
  },
  "geo_iso_heli_hover": {
    "bucket": "D",
    "target": "Image"
  },
  "geo_iso_rocket_launch": {
    "bucket": "D",
    "target": "Image"
  },
  "geo_iso_takeoff": {
    "bucket": "D",
    "target": "Image"
  },
  "geo_mercator_radar": {
    "bucket": "D",
    "target": "Image"
  },
  "globe_3d": {
    "bucket": "D",
    "target": "Image"
  },
  "isometric_mesh": {
    "bucket": "D",
    "target": "Image"
  },
  "metar_feed": {
    "bucket": "D",
    "target": "Image"
  },
  "orbit_diagram": {
    "bucket": "D",
    "target": "Image"
  },
  "skill_radar": {
    "bucket": "D",
    "target": "Image"
  },
  "benchmark_comparison": {
    "bucket": "D",
    "target": "Image"
  },
  "chartjs_bar": {
    "bucket": "D",
    "target": "Image"
  },
  "chartjs_line": {
    "bucket": "D",
    "target": "Image"
  },
  "chartjs_pie": {
    "bucket": "D",
    "target": "Image"
  },
  "confidence_bar": {
    "bucket": "D",
    "target": "Image"
  },
  "conversion_funnel": {
    "bucket": "D",
    "target": "Image"
  },
  "donut_stat": {
    "bucket": "D",
    "target": "Image"
  },
  "gauge_sla": {
    "bucket": "D",
    "target": "Image"
  },
  "github_activity_grid": {
    "bucket": "D",
    "target": "Image"
  },
  "heatmap": {
    "bucket": "D",
    "target": "Image"
  },
  "masonry_elevation": {
    "bucket": "D",
    "target": "Image"
  },
  "mini_sparkline_set": {
    "bucket": "D",
    "target": "Image"
  },
  "punch_card": {
    "bucket": "D",
    "target": "Image"
  },
  "sankey_flow": {
    "bucket": "D",
    "target": "Image"
  },
  "scatter_trend": {
    "bucket": "D",
    "target": "Image"
  },
  "sequence_diagram": {
    "bucket": "D",
    "target": "Image"
  },
  "skill_bars": {
    "bucket": "D",
    "target": "Image"
  },
  "sparkline": {
    "bucket": "D",
    "target": "Image"
  },
  "stacked_area": {
    "bucket": "D",
    "target": "Image"
  },
  "trend_indicator": {
    "bucket": "D",
    "target": "Image"
  },
  "uptime_timeline": {
    "bucket": "D",
    "target": "Image"
  },
  "word_cloud": {
    "bucket": "D",
    "target": "Image"
  },
  "comparison_morph": {
    "bucket": "D",
    "target": "Image"
  },
  "css_dropdown_menu": {
    "bucket": "D",
    "target": "Image"
  },
  "css_modal": {
    "bucket": "D",
    "target": "Image"
  },
  "css_slide_panel": {
    "bucket": "D",
    "target": "Image"
  },
  "flip_card": {
    "bucket": "D",
    "target": "Image"
  },
  "hover_card": {
    "bucket": "D",
    "target": "Image"
  },
  "image_hotspots": {
    "bucket": "D",
    "target": "Image"
  },
  "navigation_menu": {
    "bucket": "D",
    "target": "Image"
  },
  "particle_burst": {
    "bucket": "D",
    "target": "Image"
  },
  "ambient_gradient": {
    "bucket": "D",
    "target": "Image"
  },
  "animated_beam": {
    "bucket": "D",
    "target": "Image"
  },
  "animated_border": {
    "bucket": "D",
    "target": "Image"
  },
  "animated_border_card": {
    "bucket": "D",
    "target": "Image"
  },
  "animated_counter": {
    "bucket": "D",
    "target": "Image"
  },
  "aurora_background": {
    "bucket": "D",
    "target": "Image"
  },
  "badge_showcase": {
    "bucket": "D",
    "target": "Image"
  },
  "big_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "blur_fade_in": {
    "bucket": "D",
    "target": "Image"
  },
  "card_stack": {
    "bucket": "D",
    "target": "Image"
  },
  "confetti_burst": {
    "bucket": "D",
    "target": "Image"
  },
  "confetti_trigger": {
    "bucket": "D",
    "target": "Image"
  },
  "count_up_stat": {
    "bucket": "D",
    "target": "Image"
  },
  "cursor_glow": {
    "bucket": "D",
    "target": "Image"
  },
  "cursor_trail": {
    "bucket": "D",
    "target": "Image"
  },
  "depth_stack": {
    "bucket": "D",
    "target": "Image"
  },
  "dot_grid_background": {
    "bucket": "D",
    "target": "Image"
  },
  "effect_overlay": {
    "bucket": "D",
    "target": "Image"
  },
  "encrypted_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "floating_badge": {
    "bucket": "D",
    "target": "Image"
  },
  "floating_orbs": {
    "bucket": "D",
    "target": "Image"
  },
  "floating_particles": {
    "bucket": "D",
    "target": "Image"
  },
  "flow_connector": {
    "bucket": "D",
    "target": "Image"
  },
  "focus_lens": {
    "bucket": "D",
    "target": "Image"
  },
  "glitch_text": {
    "bucket": "D",
    "target": "Image"
  },
  "glow_button": {
    "bucket": "D",
    "target": "Image"
  },
  "glowing_stat": {
    "bucket": "D",
    "target": "Image"
  },
  "gradient_border_card": {
    "bucket": "D",
    "target": "Image"
  },
  "gradient_heading": {
    "bucket": "D",
    "target": "Image"
  },
  "gradient_text": {
    "bucket": "D",
    "target": "Image"
  },
  "highlight_sweep": {
    "bucket": "D",
    "target": "Image"
  },
  "hint_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "icon_liftoff": {
    "bucket": "D",
    "target": "Image"
  },
  "kinetic_headline": {
    "bucket": "D",
    "target": "Image"
  },
  "liquid_button": {
    "bucket": "D",
    "target": "Image"
  },
  "loading_dots": {
    "bucket": "D",
    "target": "Image"
  },
  "loading_skeleton": {
    "bucket": "D",
    "target": "Image"
  },
  "magnetic_button": {
    "bucket": "D",
    "target": "Image"
  },
  "magnetic_element": {
    "bucket": "D",
    "target": "Image"
  },
  "marquee": {
    "bucket": "D",
    "target": "Image"
  },
  "marquee_strip": {
    "bucket": "D",
    "target": "Image"
  },
  "mesh_gradient": {
    "bucket": "D",
    "target": "Image"
  },
  "meteor_shower": {
    "bucket": "D",
    "target": "Image"
  },
  "neon_glow": {
    "bucket": "D",
    "target": "Image"
  },
  "neon_text": {
    "bucket": "D",
    "target": "Image"
  },
  "noise_card": {
    "bucket": "D",
    "target": "Image"
  },
  "number_flip": {
    "bucket": "D",
    "target": "Image"
  },
  "number_odometer": {
    "bucket": "D",
    "target": "Image"
  },
  "parallax_card": {
    "bucket": "D",
    "target": "Image"
  },
  "parallax_section": {
    "bucket": "D",
    "target": "Image"
  },
  "pattern_background": {
    "bucket": "D",
    "target": "Image"
  },
  "progress_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "pulse_dot": {
    "bucket": "D",
    "target": "Image"
  },
  "reaction_shower": {
    "bucket": "D",
    "target": "Image"
  },
  "reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "reveal_line": {
    "bucket": "D",
    "target": "Image"
  },
  "reveal_on_scroll": {
    "bucket": "D",
    "target": "Image"
  },
  "ripple_button": {
    "bucket": "D",
    "target": "Image"
  },
  "schema_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "scramble_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "scroll_progress": {
    "bucket": "D",
    "target": "Image"
  },
  "scroll_to_top": {
    "bucket": "D",
    "target": "Image"
  },
  "scroll_trigger": {
    "bucket": "D",
    "target": "Image"
  },
  "shimmer_button": {
    "bucket": "D",
    "target": "Image"
  },
  "shimmer_text": {
    "bucket": "D",
    "target": "Image"
  },
  "skeleton_stage_card": {
    "bucket": "D",
    "target": "Image"
  },
  "sonar_pulse": {
    "bucket": "D",
    "target": "Image"
  },
  "speed_counter": {
    "bucket": "D",
    "target": "Image"
  },
  "split_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "spotlight_card": {
    "bucket": "D",
    "target": "Image"
  },
  "spotlight_cursor": {
    "bucket": "D",
    "target": "Image"
  },
  "spring_nodes": {
    "bucket": "D",
    "target": "Image"
  },
  "stagger_list": {
    "bucket": "D",
    "target": "Image"
  },
  "step_reveal_sequence": {
    "bucket": "D",
    "target": "Image"
  },
  "stripe_background": {
    "bucket": "D",
    "target": "Image"
  },
  "surface_unlocked": {
    "bucket": "D",
    "target": "Image"
  },
  "svg_path_draw": {
    "bucket": "D",
    "target": "Image"
  },
  "terminal_boot": {
    "bucket": "D",
    "target": "Image"
  },
  "text_reveal_mask": {
    "bucket": "D",
    "target": "Image"
  },
  "tilt_card": {
    "bucket": "D",
    "target": "Image"
  },
  "typewriter": {
    "bucket": "D",
    "target": "Image"
  },
  "typewriter_text": {
    "bucket": "D",
    "target": "Image"
  },
  "typing_indicator": {
    "bucket": "D",
    "target": "Image"
  },
  "wave_divider": {
    "bucket": "D",
    "target": "Image"
  },
  "word_flip": {
    "bucket": "D",
    "target": "Image"
  },
  "word_reveal": {
    "bucket": "D",
    "target": "Image"
  },
  "word_scramble": {
    "bucket": "D",
    "target": "Image"
  },
  "primitive_plate": {
    "bucket": "D",
    "target": "Image"
  },
  "action_items": {
    "bucket": "D",
    "target": "Image"
  },
  "agenda_block": {
    "bucket": "D",
    "target": "Image"
  },
  "calendar_today": {
    "bucket": "D",
    "target": "Image"
  },
  "calendar_upcoming": {
    "bucket": "D",
    "target": "Image"
  },
  "call_mood_board": {
    "bucket": "D",
    "target": "Image"
  },
  "chat_sequence": {
    "bucket": "D",
    "target": "Image"
  },
  "conversation_snippet": {
    "bucket": "D",
    "target": "Image"
  },
  "doc_ai_summary": {
    "bucket": "D",
    "target": "Image"
  },
  "drive_file_card": {
    "bucket": "D",
    "target": "Image"
  },
  "drive_file_list": {
    "bucket": "D",
    "target": "Image"
  },
  "drive_folder_contents": {
    "bucket": "D",
    "target": "Image"
  },
  "drive_image": {
    "bucket": "D",
    "target": "Image"
  },
  "drive_recent_files": {
    "bucket": "D",
    "target": "Image"
  },
  "drive_storage_usage": {
    "bucket": "D",
    "target": "Image"
  },
  "gmail_inbox": {
    "bucket": "D",
    "target": "Image"
  },
  "gmail_summary": {
    "bucket": "D",
    "target": "Image"
  },
  "gmail_unread_count": {
    "bucket": "D",
    "target": "Image"
  },
  "heatmap_calendar": {
    "bucket": "D",
    "target": "Image"
  },
  "multi_doc_ai_brief": {
    "bucket": "D",
    "target": "Image"
  },
  "sentiment_summary": {
    "bucket": "D",
    "target": "Image"
  },
  "sheet_form": {
    "bucket": "D",
    "target": "Image"
  },
  "sheet_stats": {
    "bucket": "D",
    "target": "Image"
  },
  "tasks_today": {
    "bucket": "D",
    "target": "Image"
  },
  "user_greeting": {
    "bucket": "D",
    "target": "Image"
  },
  "user_profile_card": {
    "bucket": "D",
    "target": "Image"
  },
  "workspace_logo": {
    "bucket": "D",
    "target": "Image"
  },
  "workspace_logo_grid": {
    "bucket": "D",
    "target": "Image"
  },
  "workspace_logo_strip": {
    "bucket": "D",
    "target": "Image"
  },
  "cohort_retention": {
    "bucket": "D",
    "target": "Image"
  },
  "schema_qr": {
    "bucket": "D",
    "target": "Image"
  },
  "surface_map": {
    "bucket": "D",
    "target": "Image"
  },
  "url_anatomy": {
    "bucket": "D",
    "target": "Image"
  },
  "command_palette": {
    "bucket": "D",
    "target": "Image"
  },
  "incident_log": {
    "bucket": "D",
    "target": "Image"
  },
  "service_status_board": {
    "bucket": "D",
    "target": "Image"
  },
  "stat_pulse": {
    "bucket": "D",
    "target": "Image"
  },
  "weather_now": {
    "bucket": "D",
    "target": "Image"
  },
  "weather_outlook": {
    "bucket": "D",
    "target": "Image"
  },
  "gdm_rocket_panel": {
    "bucket": "D",
    "target": "Image"
  },
  "iso_fireworks_panel": {
    "bucket": "D",
    "target": "Image"
  }
};

