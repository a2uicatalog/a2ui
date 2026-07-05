"""
gen_vocab.py — Generate OKF-compatible vocabulary markdown bundle from schema.yaml
Output: atoms/vocab/{category}.md files
"""

import yaml, os, re, textwrap
from pathlib import Path
from collections import defaultdict

SCHEMA_PATH = str(Path(__file__).parent.parent / 'atoms/schema.yaml')
OUT_DIR     = str(Path(__file__).parent.parent / 'atoms/vocab')

# Category assignments — determined by atom type name patterns and descriptions
CATEGORIES = {
    'content': [
        'intro','body','heading','subheading','quote','callout','alert_banner',
        'blockquote_with_avatar','pull_stat','footnote','glossary_term',
        'glossary_inline','text_callout','source_citation','sidebar_note',
        'caution_block','key_takeaways','summary_box','learning_objectives',
        'difficulty_badge','time_estimate','highlighted_text','abbr_tooltip',
        'inline_alert','lozenge','closing','divider',
    ],
    'lists_and_structure': [
        'bullet_list','steps','pipeline','timeline','checklist_interactive',
        'task_list','prerequisite_checklist','changelog_entry','release_notes',
        'further_reading','resources_list','key_value','table','table_of_contents',
        'breadcrumb','pagination','anchor_list','accordion_item','faq_accordion',
        'collapsible_panel','expandable_text','expandable_list','footnote_group',
        'tag_block','badge_group','status_pill','carousel','tree_view',
    ],
    'code_and_technical': [
        'code','annotated_code','code_diff','code_snippet_pair','tabbed_code',
        'terminal_block','file_tree','http_request_block','env_var_list',
        'api_reference','api_param_table','keyboard_shortcut','cli_command',
        'copy_code_block','log_output','json_tree_viewer','version_badge',
        'deprecation_notice','experimental_banner','copy_to_clipboard',
        'framed_screenshot','copy_code_button',
    ],
    'media_and_embeds': [
        'image','image_pair','image_with_caption','image_hotspots','zoomable_image',
        'gallery','video_card','video_pair','video_thumbnail','youtube',
        'audio_player','audio_link','pdf_preview','document_link',
        'embed_codepen','embed_stackblitz','embed_gist','embed_tweet',
        'embed_google_slides','figma_embed','lottie_animation','live_demo_embed',
        'color_swatch_grid','diagram',
    ],
    'data_and_charts': [
        'stat_card','metric_delta','progress_bar','progress_circle','sparkline',
        'mini_sparkline_set','trend_indicator','heatmap','heatmap_calendar',
        'punch_card','sankey_flow','cohort_retention','donut_stat','gauge_sla',
        'stacked_area','scatter_trend','chartjs_bar','chartjs_line','chartjs_pie',
        'data_table_sortable','data_grid','metric_comparison_card','benchmark_comparison',
        'feature_matrix','comparison_grid','versus_block','rating_comparison',
        'conversion_funnel','uptime_timeline','status_dashboard','github_activity_grid',
        'github_repo_card','repo_links','llm_comparison_table',
    ],
    'interactive_and_ui': [
        'tabs','tab_bar','stepper','segmented_control','toggle_switch',
        'flip_card','tooltip','hover_card','css_modal','css_dropdown_menu',
        'css_slide_panel','modal','poll_block','vote_button_group',
        'rating_stars','star_rating_input','star_rating_display','rating_summary_bar',
        'custom_checkbox_group','form','form_input','form_select','form_radio_group',
        'form_checkbox_group','form_switch_group','form_slider','form_date_picker',
        'combobox','multi_select_input','otp_input','variant_selector',
        'choicebox_group','follow_up_chips','search_result_card','command_palette',
        'navigation_menu','scroll_to_top','reading_progress_bar',
    ],
    'learning_and_gamification': [
        'quiz_question','fill_in_blank','match_exercise','hint_reveal',
        'achievement_badge','score_summary','xp_bar','lesson_nav',
        'course_progress_card','progress_checkpoint','capability_checklist',
        'shortcut_legend','prompt_template',
    ],
    'social_and_content_marketing': [
        'testimonial_card','avatar_group','contributor_list','customer_logo_grid',
        'social_proof_banner','media_mention_card','expert_endorsement',
        'review_callout','social_feed_embed','social_share_bar','newsletter_cta',
        'author_bio_card','related_posts_grid','series_overview_card',
        'reaction_group','share_quote','follow_cta','follow_button',
        'article_hero','article_series_nav','post_metadata_bar',
    ],
    'layout_and_page': [
        'before_after','side_by_side_spec','pros_cons_list','product_spec_table',
        'pricing_tier_card','pricing_tier_group','feature_grid','bento_grid',
        'cta_section','card_stack','notification_stack','notification_badge',
        'toast_notification','loading_skeleton','empty_state','spinner',
        'inline_feedback_message','action_required_card','entity_list',
        'roadmap_card','jira_ticket','sprint_board','inventory_table',
        'order_status_card','product_thumbnail',
    ],
    'animation_and_effects': [
        'animated_counter','typewriter','typewriter_text','word_flip','word_scramble',
        'number_odometer','typing_indicator','countdown_timer','gradient_text',
        'reveal_on_scroll','svg_path_draw','encrypted_reveal','sonar_pulse',
        'animated_border_card','aurora_background','dot_grid_background',
        'shimmer_button','glow_button','animated_beam','meteor_shower',
        'blur_fade_in','effect_overlay','skeleton_stage_card','marquee_strip',
        'parallax_card','toast_notification',
        'cursor_glow','cursor_trail','particle_burst','spotlight_cursor',
        'magnetic_element','tilt_card',
    ],
    'workspace_native': [
        'drive_file_list','sheet_preview','gmail_summary','calendar_upcoming',
        'user_greeting','script_run_button',
        'calendar_today','drive_recent_files','sheet_stats',
        'gmail_unread_count','user_profile_card','drive_storage_usage',
        'sheet_form_submit','tasks_today',
    ],
    'three_d_and_advanced': [
        'globe_3d','call_mood_board','sentiment_summary',
        'live_aggregator','media_stream_card',
    ],
    'ai_and_agent': [
        'model_card','conversation_snippet','llm_comparison_table',
        'confidence_bar','token_budget_meter','feedback_prompt',
        'markdown_block','doc_ai_summary','multi_doc_ai_brief',
    ],
}

CATEGORY_TITLES = {
    'content':                   'Content & Typography',
    'lists_and_structure':       'Lists, Tables & Structure',
    'code_and_technical':        'Code & Technical Reference',
    'media_and_embeds':          'Media & Embeds',
    'data_and_charts':           'Data, Charts & Metrics',
    'interactive_and_ui':        'Interactive UI & Forms',
    'learning_and_gamification': 'Learning & Gamification',
    'social_and_content_marketing': 'Social & Content Marketing',
    'layout_and_page':           'Layout & Page Components',
    'animation_and_effects':     'Animation & Visual Effects',
    'workspace_native':          'Workspace-Native (Apps Script only)',
    'three_d_and_advanced':      '3D & Advanced Visualisation',
    'ai_and_agent':              'AI & Agent Components',
}

SURFACE_LABELS = {
    'web':            'Web/Blog',
    'meet-stage':     'Meet Stage',
    'googlechat':     'Google Chat',
    'google-apps-script-web':'GAS Web App',
    'email':          'Email',
    'pdf':            'PDF',
}

def surface_badges(atom):
    s = atom.get('surfaces', {})
    works = s.get('works_on', [])
    degraded = {d['surface'] for d in s.get('degraded_on', [])} if s.get('degraded_on') else set()
    incompat = {d['surface'] for d in s.get('incompatible_on', [])} if s.get('incompatible_on') else set()
    parts = []
    for surf in ['web','meet-stage','googlechat','google-apps-script-web','email','pdf']:
        label = SURFACE_LABELS[surf]
        if surf in works:
            if surf in degraded:
                parts.append(f'`{label}*`')
            else:
                parts.append(f'**{label}**')
        # skip incompat — omission is enough
    return ' · '.join(parts) if parts else '—'

def fields_summary(atom):
    fields = atom.get('fields', {})
    if not fields:
        return '—'
    if isinstance(fields, str):
        return fields
    lines = []
    for k, v in fields.items():
        if isinstance(v, str):
            lines.append(f'`{k}` — {v}')
        elif isinstance(v, dict):
            desc = v.get('description', v.get('type', ''))
            lines.append(f'`{k}` — {desc}')
        else:
            lines.append(f'`{k}`')
    return '<br>'.join(lines)

def format_atom_row(atom):
    t = atom.get('type', '')
    desc = atom.get('compact_description', atom.get('description', ''))
    if isinstance(desc, str):
        desc = desc.split('\n')[0][:120]
    surfaces = surface_badges(atom)
    f = fields_summary(atom)
    return f'| `{t}` | {desc} | {surfaces} | {f} |'

# Load schema
with open(SCHEMA_PATH) as f:
    schema = yaml.safe_load(f)

atoms = schema.get('blocks', [])
type_to_atom = {a['type']: a for a in atoms}

# Reverse map: type -> category
type_cat = {}
for cat, types in CATEGORIES.items():
    for t in types:
        type_cat[t] = cat

# Catch uncategorised atoms
uncategorised = [a for a in atoms if a['type'] not in type_cat]

os.makedirs(OUT_DIR, exist_ok=True)

# Write one file per category
for cat, title in CATEGORY_TITLES.items():
    types_in_cat = CATEGORIES.get(cat, [])
    cat_atoms = [type_to_atom[t] for t in types_in_cat if t in type_to_atom]
    if not cat_atoms:
        continue

    surface_keys = ['google-apps-script-web','web','meet-stage','googlechat']
    support_summary = {}
    for surf in surface_keys:
        count = sum(1 for a in cat_atoms
                    if surf in a.get('surfaces', {}).get('works_on', []))
        support_summary[surf] = count

    lines = []
    lines.append(f'---')
    lines.append(f'category: {cat}')
    lines.append(f'title: {title}')
    lines.append(f'atom_count: {len(cat_atoms)}')
    lines.append(f'platform_support:')
    for surf, label in SURFACE_LABELS.items():
        count = support_summary.get(surf, 0)
        lines.append(f'  {surf}: {count}/{len(cat_atoms)}')
    lines.append(f'maturity: stable')
    lines.append(f'source: atoms/schema.yaml')
    lines.append(f'---')
    lines.append('')
    lines.append(f'# {title}')
    lines.append('')
    lines.append(f'> {len(cat_atoms)} atoms · `*` = degraded (limited support) · Bold surface = full support')
    lines.append('')
    lines.append('| Atom type | Description | Surfaces | Key fields |')
    lines.append('|-----------|-------------|----------|------------|')
    for atom in cat_atoms:
        lines.append(format_atom_row(atom))
    lines.append('')

    out_path = os.path.join(OUT_DIR, f'{cat}.md')
    with open(out_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f'  {cat}.md — {len(cat_atoms)} atoms')

# Uncategorised
if uncategorised:
    print(f'\nUncategorised ({len(uncategorised)}):')
    for a in uncategorised:
        print(f'  {a["type"]}')

print(f'\nDone. {sum(len(CATEGORIES[c]) for c in CATEGORY_TITLES)} atoms mapped across {len(CATEGORY_TITLES)} categories.')
