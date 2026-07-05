// AUTO-GENERATED — run scripts/gen_schema_snapshot.py before clasp push
// Source: atoms/schema.yaml  (apps-script-web surface only)
// Do not edit by hand.

var _ATOM_SCHEMA_SNAPSHOT = `intro  — series link or transparency note at article top
  fields: series_label: string, series_url: url, continuation: string (optional), note: string (optional)
body  — prose paragraph block
  fields: text: string
heading  — H2 section title
  fields: text: string
subheading  — H3 subsection title
  fields: text: string
quote  — pull quote or blockquote with attribution
  fields: text: string, attribution: string (optional)
code  — syntax-highlighted fenced code block
  fields: language: string, content: string
pipeline  — left-to-right step flow diagram
  fields: steps: list[string]
bullet_list  — unordered list with optional bold label per item
  fields: items ([{'label': 'string (optional)', 'text': 'string'}])
divider  — horizontal visual section break
image  — single image with optional caption
  fields: url: string, alt: string, caption: string (optional), width: string (optional)
image_pair  — two images side by side with captions
  fields: left ({'url': 'string', 'alt': 'string', 'caption': 'string (optional)'}), right ({'url': 'string', 'alt': 'string', 'caption': 'string (optional)'})
diagram  — D2 or SVG architecture diagram
  fields: url: string, caption: string (optional)
github_repo_card  — live GitHub repo card with stars forks and language
  fields: repo: string, label: string, description: string
repo_links  — styled GitHub repo link list
  fields: links ([{'label': 'string', 'url': 'string'}])
closing  — article closing paragraph with hashtags
  fields: text: string, tags: list[string] (optional)
callout  — coloured tip info warning or danger highlight box
  fields: kind: info | warning | tip | danger, title: string (optional), text: string
steps  — numbered step-by-step instruction sequence
  fields: items ([{'label': 'string (optional)', 'text': 'string'}])
table  — data table with header row on mobile
  fields: caption: string (optional), headers: list[string], rows: list[list[string]]
tabs  — tabbed content panels
  fields: accent: string (optional), tabs ([{'label': 'string', 'language': 'string', 'content': 'string'}])
key_value  — label and value pairs in a compact grid
  fields: title: string (optional), items ([{'key': 'string', 'description': 'string', 'required': 'bool (optional)', 'default': 'string (optional)'}])
before_after  — side-by-side code or content before and after comparison approach
  fields: language: string, before: string, after: string, before_label: string (optional), after_label: string (optional), caption: string (optional)
api_reference  — API endpoint method parameters and response docs returns, example
  fields: name: string, kind: function | endpoint | class | method, method: string (optional), description: string, deprecated: bool (optional), parameters ([{'name': 'string', 'type': 'string', 'required': 'bool (optional)', 'description': 'string', 'default': 'string (optional)'}]), returns: string (optional), example ({'label': 'string (optional)', 'language': 'string', 'code': 'string'})
gallery  — scrollable image gallery grid
  fields: cols: 2 | 3 | 4 (optional, default 3), caption: string (optional), images ([{'url': 'string', 'alt': 'string', 'caption': 'string (optional)'}])
video_pair  — two videos side by side
  fields: caption: string (optional), left ({'url': 'string', 'label': 'string (optional)'}), right ({'url': 'string', 'label': 'string (optional)'})
carousel  — horizontally scrollable card carousel
  fields: accent: string (optional), caption: string (optional), slides ([{'url': 'string', 'label': 'string (optional)', 'subtitle': 'string (optional)'}])
timeline  — chronological event timeline
  fields: title: string (optional), accent: string (optional), events ([{'date': 'string', 'label': 'string', 'text': 'string', 'tag': 'string (optional)'}])
annotated_code  — code block with numbered callout bubbles on specific lines explanation list below
  fields: language: string, code: string, caption: string (optional), annotations ([{'line': 'integer', 'text': 'string'}])
stat_card  — single KPI value with label delta and accent colour indicator
  fields: value: string, label: string, delta: string (optional), is_up: bool (optional), accent: string (optional)
progress_bar  — labelled horizontal progress bar with percentage
  fields: value: integer (0-100), label: string, accent: string (optional), show_percent: bool (optional), caption: string (optional)
badge_group  — row of coloured label badges
  fields: title: string (optional), badges ([{'text': 'string', 'color': 'green|cyan|blue|yellow|red|purple|grey', 'pulse': 'bool (optional)'}])
sparkline  — inline SVG trend line chart general trends.
  fields: data: list of numbers (e.g., [10, 12, 8, 15, 13]), color: string (hex or named color, e.g., '#4CAF50' or 'green'), line_width: number (e.g., 2), height: string (CSS height value, e.g., '20px'), width: string (CSS width value, e.g., '80px')
heatmap  — grid heatmap coloured by intensity value are represented as colors in a matrix.
  fields: data: list of lists of numbers (e.g., [[1, 2, 3], [4, 5, 6]]), labels_x: list of strings (labels for the x-axis, e.g., ['Mon', 'Tue', 'Wed']), labels_y: list of strings (labels for the y-axis, e.g., ['AM', 'PM']), color_scale: list of strings (colors for the gradient, e.g., ['#FFFFFF', '#FF0000'] for white to red), unit: string (optional, unit for the data values, e.g., '°C')
punch_card  — 7x24 grid of glowing activity bubbles representing hourly commits
  fields: data: list of lists of numbers (7 rows representing days of week, each containing 24 numbers representing commit frequency for each hour), labels_days: list of strings (optional, e.g., ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']), color: string (optional, hex or named color for active bubbles, e.g., '#00f2ff'), title: string (optional, title of the repository or chart, e.g., 'Commit Activity'), subtitle: string (optional, subtitle, e.g., 'curtiskrygier/meetstudio')
sankey_flow  — curved dual-column gradient flow diagram for financial or pipeline streams
  fields: nodes: list of dictionaries representing columns (e.g., [{'id': 'revenue', 'label': 'Revenue', 'column': 0, 'color': '#10b981'}, ...]), links: list of dictionaries representing flows (e.g., [{'source': 'revenue', 'target': 'marketing', 'value': 25000, 'color': '#38bdf8'}, ...]), title: string (optional, title of the chart, e.g., 'Financial Flow Allocation')
cohort_retention  — triangular cohort retention grid with continuous color-scale rendering
  fields: cohorts: list of dictionaries representing cohorts (e.g., [{'cohort_name': 'Jan 2026', 'original_size': 2500, 'retention_rates': [100.0, 93.4]}]), periods: list of strings representing period headers (e.g., ['Month 0', 'Month 1']), color_scale: list of strings representing the continuous color scale (e.g., ['#1e293b', '#10b981']), title: string (optional, chart title, e.g., 'SaaS Retention Cohorts')
donut_stat  — CSS ring chart with centre value and percentage its proportion or progress.
  fields: value: number (the current value, e.g., 75), max_value: number (the maximum possible value, e.g., 100), label: string (descriptive label for the metric, e.g., 'Completion'), unit: string (optional, unit for the value, e.g., '%'), color: string (hex or named color for the donut segment, e.g., '#2196F3'), size: string (CSS size value, e.g., '100px')
metric_delta  — big number metric with directional change indicator or percentage change from a previous period, often with an up/down indicator.
  fields: label: string (descriptive label for the metric, e.g., 'Sales'), current_value: string (the current formatted value, e.g., '$12,345'), delta_value: string (the formatted change value, e.g., '+$1,234' or '+10%'), delta_type: enum (increase, decrease, no_change) - determines icon/color, unit: string (optional, unit for the current value, e.g., 'USD'), previous_period_label: string (optional, e.g., 'vs. last month')
task_list  — glassmorphic structured checklist with priority and assignee badges
  fields: title: string (optional, e.g., 'Google Tasks & Action Items'), tasks: list of dictionaries representing tasks, where each dictionary contains: {'id': string, 'text': string, 'completed': boolean, 'priority': string (high|medium|low), 'due_date': string (optional), 'assignee': string (optional, initials e.g. 'CK')}
sentiment_summary  — meeting sentiment analyzer with index arc and timeline chart
  fields: title: string (optional, e.g., 'Call Sentiment & Mood Analysis'), sentiment_index: number representing overall positive sentiment percentage (0-100, e.g., 78), emotional_journey: list of numbers representing call sentiment score over time intervals (values -1.0 to 1.0, e.g., [0.1, -0.2, 0.4, 0.8, 0.6]), themes: list of dictionaries representing key themes with weights or moods: [{'theme': 'Technical Alignment', 'mood': 'Analytical', 'score': 85}, ...]
trend_indicator  — compact inline value with mini trend bar the direction of a trend, often accompanied by a descriptive text.
  fields: trend_direction: enum (up, down, stable) - determines the icon or arrow direction, label: string (descriptive text for the trend, e.g., 'Improving', 'Declining', 'Steady'), context: string (optional, additional context, e.g., 'over last 30 days'), color: string (optional, hex or named color for the indicator, e.g., 'green' for 'up', 'red' for 'down')
breadcrumb  — navigation breadcrumb trail structure.
  fields: items: list of {label: string, url: string, is_current: boolean}
pagination  — page number controls
  fields: current_page: integer, total_pages: integer, base_url: string (the URL prefix for all page links), page_param: string (e.g., 'page', the query parameter name for the page number)
stepper  — CSS animated vertical step sequence with checkmark draw and active pulse
  fields: steps: list of strings or {label, description} objects. Each step in the sequence., active_index: integer (optional, default 0). Index of the currently executing step. Steps before it are completed; steps after are pending., color: string (optional). Accent colour for completed/active states. Default "#38bdf8"., label: string (optional). Heading above the step list.
tab_bar  — horizontal tab navigation bar typically leading to different sections or pages.
  fields: tabs: list of {label: string, url: string, is_active: boolean, icon: string (optional, e.g., 'home')}
anchor_list  — in-page anchor navigation links document or to external URLs.
  fields: anchors: list of {label: string, url: string, target_id: string (optional, for in-document navigation on web/pdf)}
faq_accordion  — collapsible FAQ question and answer list the question is clicked.
  fields: items: list of objects, each with 'question' (string) and 'answer' (string)
glossary_term  — definition term with explanation more details.
  fields: term: string (the term itself), definition: string (the explanation), link_text: optional string (e.g., "Learn more"), link_url: optional string (URL for more details)
footnote  — numbered footnote reference at the bottom of a section or page.
  fields: number: integer (the footnote number), text: string (the footnote content), id: string (unique identifier for linking, e.g., "fn1")
blockquote_with_avatar  — testimonial quote with avatar and attribution
  fields: quote: string (the quoted text), author_name: string (name of the person quoted), author_title: optional string (title or role of the person), avatar_url: optional string (URL to the author's avatar image)
pull_stat  — large display number pulled from prose for emphasis descriptive label.
  fields: value: string (the prominent number/statistic, e.g., "99%", "1.2M"), label: string (descriptive text for the stat, e.g., "customer satisfaction"), unit: optional string (e.g., "%", "users", "USD"), color: optional string (hex code or named color for the value)
accordion_item  — single collapsible section with toggle by clicking its header, using only CSS.
  fields: header: string The title or label for the collapsible section., content: string The main content to be shown or hidden.
tooltip  — hover tooltip on a trigger element over a specified trigger element, using only CSS.
  fields: trigger_text: string The text or element that, when hovered, reveals the tooltip., tooltip_content: string The content displayed within the tooltip.
hover_card  — rich hover card revealed on mouse over specified trigger element, using only CSS.
  fields: trigger_element: string The text or element that, when hovered, reveals the card., card_title: string The title of the hover card., card_content: string The main content of the hover card, can include rich text or simple HTML., card_image_url: string, optional An optional image to display within the card.
collapsible_panel  — expandable content panel with header toggle visible and hidden states by clicking a control, using only CSS.
  fields: toggle_label: string The text for the control that expands/collapses the content., initial_state: string, default "collapsed" The initial state of the panel ("expanded" or "collapsed")., content: string The main content to be shown or hidden.
css_modal  — pure-CSS modal dialog triggered by checkbox controlled purely by CSS without JavaScript.
  fields: trigger_text: string The text or element that, when clicked, opens the modal., modal_title: string The title displayed at the top of the modal., modal_body: string The main content of the modal dialog., close_button_label: string, default "Close" The label for the button to close the modal.
audio_player  — inline audio player with controls
  fields: audio_url: string, title: string, autoplay: boolean, loop: boolean
audio_link  — styled link to an audio file
  fields: audio_url: string, label: string, icon_type: string
pdf_preview  — embedded PDF preview panel PDF.
  fields: pdf_url: string, thumbnail_url: string, title: string, alt_text: string
document_link  — styled link to a downloadable document a document icon.
  fields: document_url: string, label: string, icon_type: string
video_thumbnail  — clickable video thumbnail with play button and a link to the video source.
  fields: video_url: string, thumbnail_url: string, alt_text: string, title: string
video_card  — video with title description and metadata to the video source.
  fields: video_url: string, thumbnail_url: string, title: string, description: string, alt_text: string
code_diff  — server-side unified diff view with green additions and red removals
  fields: old_code: string. The original text (before state)., new_code: string. The updated text (after state)., label: string (optional). Title shown in the header bar., language: string (optional). Language badge shown in header, e.g. "python", "typescript"., show_line_numbers: bool (optional). Show line numbers. Default true., context_lines: integer (optional). Unchanged lines shown around each change. Default 3.
code_snippet_pair  — two code blocks side by side without diff highlighting diff highlighting.
  fields: left_code: string, right_code: string, language: string, left_label: string, right_label: string
framed_screenshot  — device-framed screenshot with optional caption browser, phone).
  fields: image_url: string, alt_text: string, device_type: string, caption: string
image_with_caption  — image with styled caption below
  fields: image_url: string, alt_text: string, caption: string, link_url: string
alert_banner  — full-width status alert strip optional action.
  fields: message: string The main message to display in the banner., type: string The type of alert (e.g., "info", "warning", "error", "success")., icon: string Optional icon name to display next to the message., action_label: string Optional text for an action button., action_url: string Optional URL for the action button.
toast_notification  — transient popup notification message automatically.
  fields: message: string The message to display in the toast., type: string The type of notification (e.g., "success", "error", "info")., duration: integer The time in milliseconds the toast should be visible.
loading_skeleton  — animated placeholder skeleton while content loads indicating active data fetching.
  fields: shape: string The general shape of the content being loaded (e.g., "card", "list", "text_block")., lines: integer The number of lines of text to simulate in the skeleton., has_image: boolean Indicates if the skeleton should include an image placeholder.
empty_state  — zero-data empty state with icon and call to action image, message, and an optional call to action.
  fields: image_url: string Optional URL for an illustrative image., title: string The main title for the empty state., description: string A descriptive message explaining why the state is empty., action_label: string Optional text for a call to action button., action_url: string Optional URL for the call to action button.
spinner  — loading spinner indicator operation is in progress.
  fields: size: string The size of the spinner (e.g., "small", "medium", "large")., color: string The color of the spinner (e.g., "primary", "gray").
status_pill  — coloured status pill badge an item.
  fields: label: string The text label for the status., color: string The semantic color of the pill (e.g., "success", "warning", "error", "info", "neutral")., icon: string Optional icon to display within the pill.
inline_feedback_message  — inline success error or warning message for validation feedback or hints.
  fields: message: string The feedback message text., type: string The type of feedback (e.g., "success", "error", "warning", "info")., icon: string Optional icon to display next to the message.
rating_stars  — star rating display stars, or displaying a static rating.
  fields: rating: integer The current rating value (e.g., 3 for 3 stars)., max_rating: integer The maximum possible rating (e.g., 5 for 5 stars)., is_interactive: boolean Indicates if the stars are clickable for user input.
progress_circle  — CSS stroke-dashoffset animated SVG progress arc with centre percentage
  fields: value: integer. The progress value (0–100)., label: string (optional). Caption text below the circle., color: string (optional). Arc stroke colour. Default "#38bdf8"., size: "sm" | "md" | "lg"  (optional, default "md"). Circle diameter.
action_required_card  — prominent card prompting a required user action user attention, with a clear call to action.
  fields: title: string The main title of the card, indicating the required action., description: string A detailed explanation of the action needed., action_label: string The text for the primary action button., action_url: string The URL for the primary action button., icon: string Optional icon to display on the card.
feature_matrix  — features versus plans comparison matrix
  fields: product_names: array, features: array
pricing_tier_card  — single pricing plan card with features list an optional call to action.
  fields: plan_name: string, price: string, currency: string, frequency: string, features: array, call_to_action_label: string, call_to_action_url: string, is_highlighted: boolean
pricing_tier_group  — side-by-side pricing plan comparison different subscription plans.
  fields: tiers: array
pros_cons_list  — two-column pros and cons comparison a single subject.
  fields: subject: string, pros: array, cons: array
side_by_side_spec  — two items compared spec by spec and values side-by-side.
  fields: item_a_name: string, item_b_name: string, specs: array
product_spec_table  — product specifications in a clean table a single product.
  fields: product_name: string, specs: array
comparison_grid  — multi-item attribute comparison grid often using icons or checkmarks to indicate presence.
  fields: products: array, features: array
versus_block  — head-to-head two-option versus card "VS" separator.
  fields: entity_a_name: string, entity_a_description: string, entity_a_image_url: string, entity_b_name: string, entity_b_description: string, entity_b_image_url: string, comparison_points: array
rating_comparison  — multiple items rated across dimensions scores.
  fields: items: array
capability_checklist  — feature capability tick list per tier capability using checkmarks or similar indicators.
  fields: capability_names: array, items: array
toggle_switch  — CSS toggle switch input
  fields: label: string, is_checked: boolean, name: string
expandable_text  — truncated text with read more expand toggle more content.
  fields: summary: string, details: string, initial_state_expanded: boolean
flip_card  — card that flips on hover to reveal back content
  fields: front_content: string, back_content: string, trigger_on_hover: boolean
image_hotspots  — image with clickable annotated hotspot overlays hover.
  fields: image_url: string, alt_text: string, hotspots: list of objects with label, x_position, y_position, content
css_dropdown_menu  — pure-CSS dropdown navigation menu
  fields: trigger_text: string, menu_items: list of objects with label, url
star_rating_input  — interactive star rating input
  fields: max_stars: integer, initial_rating: integer, name: string
segmented_control  — mutually exclusive option selector strip as a single control.
  fields: options: list of objects with label, value, selected_value: string, name: string
zoomable_image  — image with click-to-zoom lightbox
  fields: image_url: string, alt_text: string, zoom_factor: float
custom_checkbox_group  — styled checkbox group input
  fields: group_label: string, options: list of objects with label, value, is_checked, name: string
css_slide_panel  — CSS-only slide-in panel drawer activation.
  fields: trigger_text: string, panel_content: string, slide_from_side: string
testimonial_card  — customer testimonial with photo name and quote an optional avatar.
  fields: text: string, author_name: string, author_title: string, author_avatar_url: string, rating: integer
star_rating_display  — read-only star rating with score and count total review count.
  fields: rating: number, max_rating: integer, review_count: integer
avatar_group  — stacked user avatar group with overflow count or community.
  fields: avatars: list, total_count: integer, label: string
contributor_list  — list of contributors with avatar and role community, with their names, roles, and optional links or avatars.
  fields: contributors: list, title: string
customer_logo_grid  — grid of customer or partner logos
  fields: logos: list, title: string
social_proof_banner  — social proof strip with stats and logos achievement.
  fields: metric_value: string, metric_label: string, icon_url: string, link_url: string
media_mention_card  — press or media mention with logo and quote
  fields: publication_name: string, publication_logo_url: string, headline: string, article_url: string, date: string
expert_endorsement  — expert quote with credentials and photo name, and credentials.
  fields: quote: string, expert_name: string, expert_title: string, expert_organization: string, expert_avatar_url: string
review_callout  — highlighted customer review excerpt by a star rating.
  fields: review_text: string, author_name: string, rating: number, max_rating: integer, product_name: string
terminal_block  — display terminal commands and code output in a simulated console window
  fields: command: string. The execution command displayed at the prompt., output: string. The stdout or stderr text block response from the command., shell: string: bash | zsh | powershell | cmd. The console design theme.
file_tree  — present hierarchical directory structures and files for software project navigation
  fields: nodes: array. Highly structured list of folder and file objects with nesting indicators.
tabbed_code  — organize multiple programming language snippets inside an interactive tab container
  fields: tabs: array. Collection of objects containing the language identifier, tab label, and code string.
http_request_block  — document REST API endpoints with HTTP methods, headers, and payloads
  fields: method: string: GET | POST | PUT | DELETE | PATCH. The HTTP verb., url: string. The fully qualified or relative API endpoint route., headers: object. Key-value pairs detailing required HTTP headers., body: string. Optional request payload, typically stringified JSON.
env_var_list  — list configuration environment variables with descriptions and default values
  fields: variables: array. List of objects including key name, description, requirement status, and default.
prerequisite_checklist  — highlight prerequisite knowledge and system requirements before starting a tutorial
  fields: title: string. Custom header text for the prerequisite warning block., items: array. Strings containing descriptions of individual setup requirements.
keyboard_shortcut  — display visual keyboard key combinations for application shortcuts and hotkeys
  fields: keys: array. Individual key characters like Ctrl, Shift, or C to join., action: string. The function or command triggered by the keystroke combination.
api_param_table  — reference table detailing API parameters, data types, and default values
  fields: parameters: array. Objects defining name, type, required flag, default value, and description.
version_badge  — software release or dependency version number tag
  fields: version: string. The semantic version number or release label to display., status: string: stable | beta | alpha | rc. The lifecycle stage.
deprecation_notice  — warning banner for deprecated features or unsupported APIs
  fields: alternative: string. Recommended migration path or replacement feature., removal_version: string. Optional version when the feature will be removed.
experimental_banner  — highlight experimental or unstable feature notice callout
  fields: message: string. Context or feedback links for the unstable feature.
cli_command  — copyable single-line terminal command execution string
  fields: command: string. The exact shell command to be copied and executed.
copy_code_button  — button to copy specified text or code to clipboard
  fields: text_to_copy: string. The raw string content sent to clipboard when clicked.
log_output  — scrollable monospace server or compiler log output block
  fields: logs: string. The raw console log output text block.
json_tree_viewer  — expandable visual explorer for nested JSON data
  fields: data: string. The raw valid JSON string to parse and render.
key_takeaways  — highlighted summary of main conclusions and critical takeaways
  fields: points: array. Core sentences highlighting the key learnings.
summary_box  — condensed introductory panel with article overview
  fields: text: string. The summary narrative block.
learning_objectives  — checklist of educational goals and competencies gained post-reading
  fields: objectives: array. Statements describing individual knowledge achievements.
changelog_entry  — timeline entry documenting product modifications per release
  fields: version: string. The release tag or identifier., date: string. The publication date of the changes., changes: array. Objects outlining specific features modified, categorised by type.
release_notes  — grouped product release documentation by change category
  fields: title: string. Header name for the release notice., added: array. Optional new features added in this release., fixed: array. Optional bugs resolved in this release., changed: array. Optional modifications to existing behaviour.
further_reading  — curated references for extending topic research
  fields: links: array. Objects containing resource titles, URLs, and brief annotations.
resources_list  — downloadable project assets and attached resource links
  fields: items: array. Download assets containing title, size, type, and url.
sidebar_note  — off-axis container for peripheral notes or caveats
  fields: title: string. The headline for the side note., content: string. The note content.
difficulty_badge  — label technical complexity level of blog content
  fields: level: string: beginner | intermediate | advanced. The target audience expertise tier.
caution_block  — highlight dangerous pitfalls or critical destructive actions
  fields: message: string. The warning content.
checklist_interactive  — interactive task tracking checklist for article milestones
  fields: items: array. Individual checkpoint task strings.
glossary_inline  — inline hover tooltips for complex technical term definitions
  fields: term: string. The technical phrase needing definition., definition: string. Explanation displayed when term is activated.
time_estimate  — estimated reading duration badge for article content
  fields: minutes: integer. The estimated reading time in minutes.
progress_checkpoint  — milestone progress indicator across multi-step tutorial
  fields: current_step: integer. The current active step index., total_steps: integer. Total steps in the sequence.
social_share_bar  — social media buttons for sharing article to external networks
  fields: platforms: array. Permitted networks: twitter | linkedin | facebook | reddit., url: string. Optional URL override, defaults to current page.
newsletter_cta  — email subscription form for recurring reader updates
  fields: headline: string. Header message prompting subscription., button_label: string. Optional submit button text, defaults to Subscribe.
author_bio_card  — profile block displaying content creator biographical details
  fields: name: string. Full name of the content creator., avatar_url: string. URL to the profile image., bio: string. Short narrative profiling the writer., links: object. Optional key-value pairs of platform names and URLs.
related_posts_grid  — grid of recommended alternative post reading cards
  fields: posts: array. Objects containing title, url, and optional topic.
series_overview_card  — navigation index for multi-part article series parts
  fields: series_name: string. Name of the series., parts: array. Objects with title, url, and optional current boolean.
reaction_group  — emoji reaction counters collecting reader sentiment feedback
  fields: enabled_emojis: array. Tracked emojis: thumbs_up | heart | rocket | mind_blown.
share_quote  — prominent blockquote optimised for social media sharing
  fields: text: string. The impactful quote statement., author: string. Optional attribution source.
follow_cta  — call to action driving social media community expansion
  fields: message: string. Promotional copy driving user interactions., platform_links: object. Platform name keys mapped to target URLs.
follow_button  — direct profile subscription button for social platforms
  fields: target_handle: string. Handle identifier of target profile., platform: string: twitter | github | linkedin. The platform.
reading_progress_bar  — track and display article reading progress completion status
  fields: color: string. Hexadecimal or design utility color token for the bar.
table_of_contents  — navigate article sections using structured heading directory links
  fields: headings: array. Structured items detailing section names and anchor tags.
article_hero  — display prominent introductory headline and banner media
  fields: title: string. Main showcase headline text., subtitle: string. Optional accompanying summary text., image_url: string. URL to header background media.
scroll_to_top  — quickly return viewport to top of page document
  fields: behavior: string: smooth | auto. Scroll animation profile.
article_series_nav  — navigate interconnected parts inside multi-part blog series
  fields: series_id: string. Unique identifier of the series cluster., current_part: integer. Ordered index within series limits.
color_swatch_grid  — grid of named color swatches with hex values
  fields: colors: array of {name, hex}. Color entries to display.
benchmark_comparison  — side-by-side performance benchmark comparison bars
  fields: items: array of {label, value}. Benchmark entries.
chartjs_bar  — interactive Chart.js bar chart with datasets
  fields: labels: array of strings. X-axis labels., datasets: array of {label, data}. Chart datasets.
chartjs_line  — interactive Chart.js line chart for trend data
  fields: labels: array of strings. X-axis labels., datasets: array of {label, data}. Chart datasets.
data_table_sortable  — sortable data table with column headers
  fields: headers: array of strings. Column headers., rows: array of arrays. Table rows.
metric_comparison_card  — metric card comparing current vs previous period
  fields: label: string. Metric name., value: number. Current value., previous: number. Previous period value.
mini_sparkline_set  — compact grid of multiple labeled sparklines
  fields: series: array of {label, data}. Sparkline series.
status_dashboard  — grid of service status indicators with color states
  fields: metrics: array of {label, value, color}. Status entries.
uptime_timeline  — 30-day uptime timeline with per-day status blocks
  fields: uptime: number. Uptime percentage (0–100).
command_palette  — keyboard-driven command palette with shortcut hints
  fields: commands: array of {text, shortcut}. Available commands.
search_result_card  — single search result card with title snippet URL
  fields: title: string. Result title., description: string. Snippet text., url: string (optional). Result URL.
post_metadata_bar  — article metadata bar with author date read time
  fields: author: string. Author display name., date: string. Publish date (YYYY-MM-DD)., readTime: integer. Estimated read time in minutes.
footnote_group  — numbered footnote list at section or article end
  fields: footnotes: array of {id, text}. Footnote entries.
notification_badge  — unread count badge overlaid on icon element
  fields: text: string. Badge label or count., color: string (optional). Background colour (hex).
expandable_list  — nested expandable tree list with collapsible children
  fields: items: array of {text, children}. Tree nodes.
poll_block  — poll with question options and vote count bars
  fields: question: string. Poll question., options: array of {text, votes}. Poll choices.
abbr_tooltip  — inline abbreviation with hover tooltip full form
  fields: text: string. The abbreviation to display., title: string. The expanded full form.
copy_to_clipboard  — copy-to-clipboard button with inline code and feedback
  fields: text: string. Display label., value: string. Value copied to clipboard.
conversion_funnel  — pipeline conversion funnel with step tapering and leak markers
  fields: title: string (optional, e.g., 'Acquisition Funnel'), steps: list of dictionaries representing funnel stages: [{'stage': 'Visits', 'value': 10000}, {'stage': 'Signups', 'value': 4500}, ...]
gauge_sla  — radial SLA gauge with glowing pointer and large metric value
  fields: title: string (optional, e.g., 'API Response SLA'), value: number representing current value (e.g., 99.4), max_value: number representing maximum gauge scale (e.g., 100), unit: string (optional, e.g., '%'), label: string (optional, e.g., 'SLA Met')
stacked_area  — stacked area chart with overlapping glowing translucent gradients
  fields: title: string (optional, e.g., 'SaaS Cumulative Workloads'), labels: list of strings representing X-axis ticks (e.g., ['Q1', 'Q2', 'Q3', 'Q4']), series: list of dictionaries representing stacked layers: [{'label': 'Enterprise', 'data': [10, 25, 45, 60], 'color': '#00f2ff'}, ...]
scatter_trend  — coordinate scatter plot with regression trend line
  fields: title: string (optional, e.g., 'CSAT vs. Support Response Time'), data_points: list of [x, y] coordinates: [[1.2, 95], [2.5, 88], [3.1, 75]], label_x: string (optional, e.g., 'Response Time (Hours)'), label_y: string (optional, e.g., 'CSAT Score')
call_mood_board  — visual summary board of call sentiments moods and active themes
  fields: title: string (optional, e.g., 'Call Mood & Themes Summary'), moods: list of dictionaries representing call emotions: [{'mood': 'Collaborative', 'intensity': 85, 'color': '#10b981'}, ...], themes: list of dictionaries representing keywords/themes: [{'term': 'Pricing', 'weight': 90, 'sentiment': 'neutral'}, ...], summary: string (optional summary paragraph)
github_activity_grid  — SVG GitHub-style contribution grid and activity tracker
  fields: title: string (optional, e.g., 'GitHub Repository Activity'), username: string (optional, e.g., 'curtiskrygier'), total_contributions: integer (optional, e.g., 342), streak_days: integer (optional, e.g., 18), activity: list of integers (0-4) or dictionary of weeks/days for rendering grid squares
form  — labelled form with fields and submit button
  fields: title: string (optional). Form heading shown above fields., submit_label: string (optional, default 'Submit'). Label for the primary submit button., cancel_label: string (optional). If set, renders a secondary cancel button., fields ({'type': 'array', 'items': {'label': 'string. Visible field label.', 'name': 'string. Field identifier used in form submission.', 'type': 'string. One of: text, email, password, number, url, textarea, select, radio, checkbox, switch, slider, date. Default: text.', 'placeholder': 'string (optional).', 'options': 'array of {value, label} (required for select, radio, checkbox types).', 'default_value': 'string | boolean | number (optional).', 'rules': "array of strings (optional). Validation rules e.g. ['required', 'email', 'minLength:2']."}})
form_input  — single labelled input field
  fields: label: string. Visible label above the input., name: string. Field identifier., type: string (optional). One of: text, email, password, number, url. Default: text., placeholder: string (optional)., rules: array of strings (optional). e.g. ['required', 'email', 'minLength:2'].
form_select  — labelled dropdown select with options
  fields: label: string. Visible label., name: string. Field identifier., placeholder: string (optional). e.g. 'Select an option…', options ({'type': 'array', 'description': 'List of {value, label} pairs.'}), rules: array of strings (optional). e.g. ['required'].
form_radio_group  — radio button group for single-option selection
  fields: label: string (optional). Group label., name: string. Field identifier., options ({'type': 'array', 'description': 'List of {value, label, description?} entries.'}), default_value: string (optional). Pre-selected option value., rules: array of strings (optional). e.g. ['required'].
form_checkbox_group  — checkbox group for multi-option selection
  fields: label: string (optional). Group label., name: string. Aggregate field identifier for form submission., items ({'type': 'array', 'description': 'List of {name, label, description?, default_checked?} entries.'}), rules: array of strings (optional).
form_switch_group  — group of labelled toggle switches
  fields: label: string (optional). Section label above the switches., name: string. Aggregate field identifier., items ({'type': 'array', 'description': 'List of {name, label?, description?, default_checked?} entries.'})
form_slider  — numeric range slider input
  fields: label: string (optional). Visible label above the slider., name: string. Field identifier., min: number. Minimum value., max: number. Maximum value., step: number (optional). Increment size. Omit for continuous., default_value: number (optional). Initial thumb position., variant: string (optional). One of: continuous, discrete. Default: continuous., rules: array of strings (optional).
form_date_picker  — date or date-range picker input
  fields: label: string (optional). Visible label., name: string. Field identifier., mode: string (optional). One of: single, range. Default: single., placeholder: string (optional). e.g. 'Pick a date'., rules: array of strings (optional). e.g. ['required'].
modal  — modal dialog overlay with title and content
  fields: title: string. Modal heading., size: string (optional). One of: sm, md, lg. Default: md., children ({'type': 'array', 'description': 'Content atoms to render inside the modal body.'}), trigger_label: string (optional). If set, renders a button that opens the modal.
follow_up_chips  — clickable follow-up suggestion chips
  fields: items ({'type': 'array', 'description': "List of suggestion strings. e.g. ['What's the ROI?', 'Show me by region', 'Compare to last year']."}), label: string (optional). Small heading above the chips. e.g. 'You might also ask:'
choicebox_group  — card-style option selector with icon, title, description per card
  fields: label: string (optional). Group heading above the cards., name: string. Form field name for the selected value(s)., multiple: boolean (optional, default false). If true allows multiple selections., accent: string (optional, default, submit_label: string (optional). If set, renders a submit button below the cards., items ({'type': 'array', 'description': 'List of {value, title, description?, icon?, disabled?} entries.'})
feedback_prompt  — thumbs or star rating feedback collection widget
  fields: question: string (optional). Label text above the widget. e.g. "Was this helpful?", style: string (optional). One of: thumbs | stars. Default: thumbs., placeholder: string (optional). Follow-up textarea placeholder shown after the rating buttons., action_url: string (optional). Endpoint for form POST on submit.
entity_list  — named resource rows with avatar, status badge, and meta
  fields: items ({'type': 'array', 'description': 'List of {name, subtitle?, icon?, status?, meta?} entries.'})
prompt_template  — LLM prompt with highlighted {variable} slots and copy button
  fields: template: string. The prompt text containing {slot} placeholders., accent: string (optional, default, copyable: boolean (optional, default true). Show copy button., label: string (optional). Small label shown above the template block.
model_card  — AI model spec card with context window, pricing, and capability badges
  fields: name: string. Model display name, e.g. "Claude Sonnet 4.6"., provider: string (optional). Provider name, e.g. "Anthropic"., context_window: string (optional). e.g. "200 k tokens"., pricing: string (optional). e.g. "$3 / M tokens in"., capabilities ({'type': 'array', 'description': 'List of short capability badge strings, e.g. ["tool use", "vision", "streaming"].'}), accent: string (optional, default #7c3aed). Accent colour for provider label and badges.
conversation_snippet  — user prompt and AI response as chat bubbles
  fields: user_label: string (optional, default "You"). Label above the user bubble., user: string. The user prompt text., ai_label: string (optional, default "Assistant"). Label above the AI bubble., response: string. The AI response text., accent: string (optional, default
shortcut_legend  — keyboard shortcut cheat-sheet grid with key combos and labels
  fields: title: string (optional). Heading above the grid., items ({'type': 'array', 'description': 'List of {keys, action} entries. keys is an array of key strings e.g. ["⌘", "K"]. action is the human-readable description.'})
rating_summary_bar  — star rating histogram with percentage bars per star level
  fields: average: number. Overall average rating (e.g. 4.3)., total: number. Total number of ratings., breakdown ({'type': 'array', 'description': 'List of {stars, count} from 5 down to 1.'}), accent: string (optional, default
roadmap_card  — quarter-based product roadmap with status-tagged milestones
  fields: title: string (optional). Heading above the roadmap., periods ({'type': 'array', 'description': 'List of {label, items} where each item is {text, status}. status is one of done | in-progress | planned.'})
notification_stack  — persistent notification inbox list with unread indicators
  fields: title: string (optional). Heading above the list, e.g. "Notifications"., items ({'type': 'array', 'description': 'List of {icon?, title, body?, time?, unread?} entries. unread is boolean, default false.'})
inline_alert  — inline icon-plus-text alert embedded in content flow
  fields: type: string. Severity level — "info", "warning", "error", or "success"., message: string. The alert text., detail: string (optional). A secondary line of smaller detail text., icon: string (optional). Override the default icon for the severity type.
tag_block  — horizontal wrap of neutral content chip labels
  fields: tags: array of strings. The tag labels., color: string (optional). Override chip accent — hex or CSS colour. Default is neutral gray.
variant_selector  — CSS radio card group for variant or option picking
  fields: name: string. Form field name used in radio input group., label: string (optional). Group label shown above the options., items ({'type': 'array', 'description': 'List of {value, title, description?} option objects.'}), default_value: string (optional). Pre-selected option value.
markdown_block  — GFM markdown string rendered to HTML inline
  fields: content: string. The Markdown source string to render., variant: string (optional). "default" (standard margins) or "compact" (tight spacing for dense layouts). Default is "default".
chartjs_pie  — multi-slice pie or donut SVG chart with legend
  fields: title: string (optional). Chart heading., variant: string (optional). "pie" or "donut". Default "donut"., data ({'type': 'array', 'description': 'List of {label, value} slice objects.'}), colors: array of strings (optional). Hex colours per slice; auto-assigned if omitted., show_legend: boolean (optional). Show colour-keyed legend below chart. Default true., show_labels: boolean (optional). Show percentage labels on slices. Default true.
text_callout  — lightweight tinted inline tip or note block no icon
  fields: variant: string. Display variant — "info", "success", "warning", "neutral"., title: string. Short bold label (e.g. "Tip", "Note", "Good to know")., description: string. Body text.
source_citation  — numbered RAG source card with title excerpt and URL
  fields: sources ({'type': 'array', 'description': 'List of {number, title, url?, excerpt?, author?, date?} citation objects.'}), heading: string (optional). Section heading above the list, e.g. "Sources".
llm_comparison_table  — side-by-side multi-model output comparison table
  fields: prompt: string (optional). The shared input prompt shown above the comparison., models ({'type': 'array', 'description': 'List of {name, output, latency_ms?, cost_usd?, tokens?} model result objects.'}), show_meta: boolean (optional). Show latency/cost/token row below each output. Default true if any model provides meta fields.
confidence_bar  — labelled probability bar with colour-coded confidence fill
  fields: label: string. What is being measured, e.g. Positive Sentiment or Retrieval Relevance., value: number. Confidence percentage 0-100., items: array (optional). List of {label, value} for multi-row display instead of single bar., color: string (optional). Override bar fill colour. Auto-assigned green/amber/red by value band if omitted.
token_budget_meter  — context window token usage meter with capacity warning colours
  fields: used: integer. Tokens consumed so far., total: integer. Model context window size, e.g. 200000., model: string (optional). Model name shown as subtitle, e.g. "claude-sonnet-4-6"., label: string (optional). Override the default "Context window" heading., warn_at: number (optional). Percentage threshold to shift to amber. Default 70., critical_at: number (optional). Percentage threshold to shift to red. Default 90., animate: boolean (optional). Count up from 0 to \`used\` using CSS @property animation. Bar grows in sync. Uses dark styling suited to Meet stage. Default false (static)., duration: number (optional). Animation duration in seconds when animate is true. Default 2.0.
product_thumbnail  — product card with image, price, status badge, and tags
  fields: title: string. Product display name., vendor: string (optional). Brand or supplier name., sku: string (optional). Stock-keeping unit code., price: string. Formatted price, e.g. "$49.00"., compare_at_price: string (optional). Strike-through original price., status: string (optional). One of active | draft | archived. Default active., image_url: string (optional). Product image URL., tags: array of strings (optional). Flat tag list rendered as chips.
order_status_card  — e-commerce order card with status badge and line item list
  fields: order_number: string. Order identifier, e.g. "#1042"., date: string (optional). Order date displayed next to the order number., status: string. One of fulfilled | unfulfilled | partial | cancelled | refunded., customer: string (optional). Customer display name., items: array (optional). List of {title, qty, price} line items., total: string (optional). Formatted grand total, e.g. "$124.00".
inventory_table  — inventory table with SKU, stock levels, and low-stock row highlight
  fields: title: string (optional). Table heading., items: array. List of {sku?, product, available, committed?, location?, threshold?}. threshold triggers amber low-stock highlight when available < threshold.
jira_ticket  — Jira issue card with type icon, status lozenge, priority, and assignee
  fields: key: string. Issue key, e.g. "PROJ-123"., issue_type: string (optional). One of bug | story | task | epic | subtask. Default task., summary: string. Issue title or one-line description., status: string (optional). Column name e.g. "To Do", "In Progress", "Done"., priority: string (optional). One of highest | high | medium | low | lowest., assignee: string (optional). Assignee display name., description: string (optional). Short description or acceptance criteria., labels: array of strings (optional). Label chips shown below the description.
sprint_board  — kanban sprint board with named columns and compact issue cards
  fields: sprint_name: string (optional). Sprint label shown above the board., columns: array. List of {name, items[]} where each item is {key, summary, type?, priority?}.
lozenge  — Atlassian-semantic status pill with defined appearance variants
  fields: text: string. The lozenge label (single lozenge mode)., appearance: string (optional). One of default | success | removed | inprogress | moved | new. Default default., items: array (optional). List of {text, appearance} for a row of multiple lozenges. Overrides single text/appearance fields.
data_grid  — enterprise data grid with typed columns, row selection, and pagination
  fields: title: string (optional). Dark header bar above the grid., columns: array. List of {header, key, type?, sortable?}. type is one of string | number | status | tag., rows: array. List of row objects where each key matches a column key., selectable: boolean (optional). Show row-selection checkboxes. Default false., pagination: object (optional). '{per_page} splits rows into CSS-tab pages; clicking a page number label switches pages without JavaScript. Omit for single-page display.'
tree_view  — recursive hierarchical tree with expand/collapse per node
  fields: title: string (optional). Label above the tree panel., nodes: array. Recursive list of {label, icon?, expanded?, meta?, children?[]} node objects.
heatmap_calendar  — calendar month heatmap with date-value density colouring
  fields: title: string (optional). Heading above the calendar grid., data: array. List of {date, count} objects where date is "YYYY-MM-DD"., months: integer (optional). Number of calendar months to render. Default 3., color_scale: array of strings (optional). CSS colours from empty to maximum density. Default IBM Carbon blue scale., unit: string (optional). Unit label appended to count in tooltips, e.g. "commits".
combobox  — searchable filterable dropdown — shadcn/Headless UI pattern
  fields: label: string (optional). Visible label above the field., name: string. Field identifier., placeholder: string (optional). Input placeholder text., options: array of {value, label} pairs., selected: string (optional). Pre-selected option value., rules: array of strings (optional). e.g. ['required'].
feature_grid  — icon + title + description feature grid — Tailwind UI pattern
  fields: heading: string (optional). Section heading above the grid., description: string (optional). Section sub-heading or intro paragraph., columns: integer (optional). 2 or 3. Default 3., features: array of objects with fields — icon (emoji or text), title, description, badge (optional short label), color (optional hex accent).
navigation_menu  — multi-level horizontal nav with submenu panels — Radix pattern
  fields: brand: string (optional). Brand name shown on the left., brand_url: string (optional). URL for the brand link., items: array of objects with — label, url, children (optional array of {label, url, description})., cta: object (optional). {label, url} for a right-aligned call-to-action button.
multi_select_input  — chip-style multi-value select input — shadcn pattern
  fields: label: string (optional). Visible label above the field., name: string. Field identifier., placeholder: string (optional). Input placeholder when no chips are selected., options: array of {value, label} pairs., selected: array of value strings. Pre-selected values shown as chips.
otp_input  — N-box one-time password digit input — shadcn OTP pattern
  fields: length: integer (optional). Number of digit boxes. Default 6., value: string (optional). Pre-filled digits., label: string (optional). Visible label above the boxes.
bento_grid  — asymmetric bento-box feature tile grid — MagicUI/shadcn pattern
  fields: heading: string (optional). Section heading above the grid., columns: integer (optional). Number of grid columns. Default 3., tiles: array of objects with — title, subtitle, icon (emoji), span (integer, default 1; span 2 fills two columns), color (optional hex), background (optional hex).
cta_section  — full-width CTA banner with headline and buttons — Tailwind UI pattern
  fields: heading: string. Main headline., body: string. Descriptive paragraph., primary_cta: object. {label, url} for the primary action button., secondary_cta: object (optional). {label, url} for a ghost secondary button., background: string (optional). CSS color for the banner background. Default
animated_counter  — CSS-only animated counter that counts up to target values
  fields: counters: array of objects with — value (integer), label, prefix (optional), suffix (optional), color (optional hex)., duration: number (optional). Animation duration in seconds. Default 2.
media_stream_card  — Auto-detecting YouTube/Loom/Slides/Vimeo embed with skeleton loader
  fields: url: string (required). Raw URL — YouTube, Loom, Google Slides, Vimeo, or any embeddable URL. Platform is auto-detected., title: string (optional). Card label shown above the iframe. Defaults to detected platform name., height: string (optional). CSS height for the iframe container. Default 360px.
live_aggregator  — Real-time comparative bars for votes, counts, or percentages
  fields: items: array of objects — label (string), value (number), color (optional hex)., title: string (optional). Section heading above the bars., max_value: number (optional). Denominator for bar widths; auto-computed from max item value if omitted., show_values: boolean (optional). Show numeric value next to each bar. Default true.
vote_button_group  — Multi-option vote buttons in pill, neon, or default style
  fields: options: array of objects — label (string), value (string), selected (boolean optional)., style: string (optional). One of pill, neon, default. Default pill., title: string (optional). Section heading above the buttons., allow_multi: boolean (optional). Allow multiple selections. Default false.
effect_overlay  — CSS confetti/trophy/pulse celebration overlay triggered by name
  fields: trigger: string (required). One of confetti, trophy, pulse, fireworks., status: string (optional). Small label shown above the effect (e.g. resolved, done)., message: string (optional). Text shown below the icon., color: string (optional). Primary accent color for pulse effect. Default
skeleton_stage_card  — Dark shimmer skeleton loader in card/list/media/chat variants
  fields: variant: string (optional). One of card, list, media, chat. Default card., lines: integer (optional). Number of text lines or list rows to show. Default 3., count: integer (optional). Number of skeleton cards to stack. Default 1.
marquee_strip  — infinite CSS-animated horizontal marquee of text or logo items
  fields: items: array. Each item is a string or {text, image_url} object., speed: "slow" | "normal" | "fast"  (optional, default "normal"), direction: "left" | "right"  (optional, default "left"), pause_on_hover: bool (optional, default true). Pause scroll on hover., label: string (optional). Small header label above the strip., gap: string (optional). CSS gap between items. Default "40px".
typewriter_text  — CSS typewriter animation that reveals text character by character
  fields: text: string. The text to type out., size: string (optional). Font size e.g. "32px". Default "28px"., weight: string (optional). Font weight e.g. "700". Default "700"., color: string (optional). Text colour. Default "#1a1a1a"., speed: "slow" | "normal" | "fast"  (optional, default "normal"), cursor: bool (optional). Show blinking cursor. Default true., delay: string (optional). CSS delay before typing starts. Default "0s".
animated_border_card  — card with CSS rotating gradient animated border
  fields: title: string (optional). Card heading., body: string. Card body content (markdown inline formatting supported)., accent: string (optional). Primary border gradient colour. Default "#38bdf8"., accent2: string (optional). Secondary border gradient colour. Default "#818cf8"., background: string (optional). Inner card background colour. Default "#ffffff"., speed: "slow" | "normal" | "fast"  (optional, default "normal"), border_width: integer (optional). Border thickness in px. Default 2.
aurora_background  — animated aurora borealis gradient blob background, CSS-only
  fields: colors: array of up to 3 hex colour strings (optional). Default ["#38bdf8","#818cf8","#34d399"]., speed: "slow" | "normal" | "fast"  (optional, default "slow"), opacity: float 0–1 (optional, default 0.5). Blob layer opacity., background: string (optional). Panel background colour. Default "#0a0f1d"., title: string (optional). Text heading overlaid on the aurora., body: string (optional). Body text overlaid on the aurora (markdown inline supported).
dot_grid_background  — CSS repeating dot or grid pattern panel background
  fields: variant: "dots" | "grid" | "cross"  (optional, default "dots"), title: string (optional). Text heading overlaid on the pattern., body: string (optional). Body text overlaid on the pattern (markdown inline supported)., dot_color: string (optional). Dot or line colour. Default "rgba(148,163,184,0.35)"., background: string (optional). Panel background fill. Default "#0d1525"., spacing: integer (optional). Grid cell size in px. Default 24., dot_size: integer (optional). Dot radius in px (dots variant only). Default 1.
shimmer_button  — button with CSS background-position shimmer sweep animation
  fields: label: string. Button text., href: string (optional). If set, renders as an anchor tag., size: "sm" | "md" | "lg"  (optional, default "md"), accent: string (optional). Shimmer highlight colour. Default "#38bdf8"., background: string (optional). Button background colour. Default "#1e293b"., speed: "slow" | "normal" | "fast"  (optional, default "normal"), description: string (optional). Small text below the button.
card_stack  — CSS-fanned stack of 2–4 cards with rotation and opacity tiers
  fields: cards: array. Each card: {title, body, accent}. Max 4 cards., background: string (optional). Card background colour. Default "#1e293b"., border_color: string (optional). Card border colour. Default "rgba(255,255,255,0.08)"., height: integer (optional). Card height in px. Default 160.
meteor_shower  — CSS-animated diagonal falling meteor streaks on a dark panel
  fields: count: integer (optional). Number of meteors. Default 20. Max 40., color: string (optional). Meteor streak colour. Default "#38bdf8"., speed: "slow" | "normal" | "fast"  (optional, default "normal"), background: string (optional). Panel background colour. Default "#0a0f1d"., title: string (optional). Text heading overlaid on the effect., body: string (optional). Body text overlaid on the effect (markdown inline supported).
blur_fade_in  — CSS blur-to-focus fade-in container reveal
  fields: children: array of atom objects to render inside the container (optional)., title: string (optional). Heading text., body: string (optional). Body text (markdown inline supported)., delay: string (optional). CSS delay before animation starts, e.g. "0.3s". Default "0s"., speed: "slow" | "normal" | "fast"  (optional, default "normal"), direction: "up" | "down" | "left" | "right" | "none"  (optional, default "up"). Drift direction on reveal., blur: string (optional). Starting blur radius, e.g. "8px". Default "8px"., background: string (optional). Panel background. Default transparent.
glow_button  — CSS box-shadow state-signalling button with disabled/ready/fired glow
  fields: label: string. Button text., state: "disabled" | "ready" | "fired"  (optional, default "ready"), href: string (optional). If set renders as an anchor tag., color_ready: string (optional). Glow colour in ready state. Default "#38bdf8"., color_fired: string (optional). Glow colour in fired state. Default "#34d399"., size: "sm" | "md" | "lg"  (optional, default "md"), description: string (optional). Small caption text below the button.
animated_beam  — CSS stroke-dashoffset animated SVG beam between two labelled nodes
  fields: from_label: string. Left/source node label., to_label: string. Right/target node label., label: string (optional). Small caption above the beam diagram., body: string (optional). Description text below the diagram., active: bool (optional). Whether the beam pulse animates. Default true., color: string (optional). Beam and node accent colour. Default "#38bdf8"., speed: "slow" | "normal" | "fast"  (optional, default "normal"), curved: bool (optional). Use a curved cubic-bezier path. Default true.
encrypted_reveal  — CSS steps() scramble-to-reveal text animation
  fields: text: string. The final text to reveal., size: string (optional). Font size e.g. "32px". Default "28px"., weight: string (optional). Font weight. Default "700"., color: string (optional). Text colour. Default "#f1f5f9"., scramble_color: string (optional). Colour of scramble characters. Default "#38bdf8"., speed: "slow" | "normal" | "fast"  (optional, default "normal"), delay: string (optional). CSS delay before reveal starts. Default "0s"., frames: integer (optional). Number of scramble frames before lock. Default 8., background: string (optional). Container background. Default transparent.
word_flip  — CSS steps() vertical word carousel in an overflow-hidden inline container
  fields: words: array of strings. The words to cycle through. Minimum 2., prefix: string (optional). Static text before the flipping section, e.g. "Grow your "., suffix: string (optional). Static text after the flipping section., speed: "slow" | "normal" | "fast"  (optional, default "normal"). Per-word hold duration., color: string (optional). Flipping word colour. Default "#38bdf8"., size: string (optional). Font size, e.g. "32px". Default "inherit"., weight: string (optional). Font weight of flipping words. Default "700".
sonar_pulse  — CSS concentric ring pulse animation for attention signalling
  fields: variant: "critical" | "success" | "info" | "warning"  (optional, default "critical"), active: bool (optional). If false renders as a static dot. Default true., label: string (optional). Short text label centred in the pulse ring., size: "sm" | "md" | "lg"  (optional, default "md"). Controls ring diameter., body: string (optional). Caption text below the pulse ring.
typewriter  — CSS character-by-character typewriter reveal with optional cursor
  fields: text: string. The text to type out., speed: "slow" | "normal" | "fast"  (optional, default "normal"), cursor: bool (optional). Show blinking cursor after typing. Default true., color: string (optional). Text colour. Default "#0f172a"., size: string (optional). Font size e.g. "1.4rem". Default "1.4rem"., weight: string (optional). Font weight. Default "600"., background: string (optional). Container background. Default "#f8fafc".
number_odometer  — Slot-machine digit-column flip to target number
  fields: value: string. The target number to display e.g. "1337" or "42.5k"., label: string (optional). Caption below the number., color: string (optional). Digit colour. Default "#0f172a"., accent: string (optional). Accent colour. Default "#4f46e5"., size: string (optional). Font size. Default "3rem"., duration: number (optional). Animation duration in seconds. Default 1.2.
typing_indicator  — Three-dot bouncing chat typing indicator bubble
  fields: name: string (optional). Agent or user name shown above the bubble. Default "Agent"., variant: "dark" | "light"  (optional, default "dark"). Bubble colour scheme.
countdown_timer  — Flip-clock countdown timer display (static tiles, data-driven ticking)
  fields: hours: integer (optional). Hours component. Default 0., minutes: integer (optional). Minutes component. Default 4., seconds: integer (optional). Seconds component. Default 59., label: string (optional). Caption below the timer., variant: "dark" | "light"  (optional, default "dark")., accent: string (optional). Separator and accent colour. Default "#00f2ff".
gradient_text  — Animated gradient-fill heading text via CSS background-clip
  fields: text: string. The heading text to display., from: string (optional). Gradient start colour. Default "#4f46e5"., to: string (optional). Gradient end colour. Default "#06b6d4"., via: string (optional). Optional midpoint colour., size: string (optional). Font size. Default "2rem"., weight: string (optional). Font weight. Default "800"., duration: number (optional). Cycle duration in seconds. Default 4.
reveal_on_scroll  — IntersectionObserver scroll-triggered fade+slide reveal
  fields: title: string (optional). Bold heading inside the block., body: string (optional). Body text inside the block., direction: "up" | "down" | "left" | "right"  (optional, default "up"). Drift direction before reveal., duration: number (optional). Transition duration in seconds. Default 0.7., accent: string (optional). Left border accent colour. Default "#4f46e5"., background: string (optional). Block background. Default "#f8fafc".
word_scramble  — CSS steps() left-to-right character scramble-to-reveal
  fields: text: string. The final text to reveal., duration: number (optional). Total animation duration in seconds. Default 2.0., color: string (optional). Final text colour. Default "#0f172a"., scramble_color: string (optional). Scramble character colour. Default "#4f46e5"., size: string (optional). Font size. Default "2.5rem"., weight: string (optional). Font weight. Default "800".
svg_path_draw  — SVG stroke-dashoffset self-drawing path animation
  fields: shape: "arrow" | "check" | "circle" | "zigzag" | "infinity"  (optional, default "arrow"), color: string (optional). Stroke colour. Default "#4f46e5"., width: integer (optional). Stroke width in px. Default 3., duration: number (optional). Draw duration in seconds. Default 1.5., label: string (optional). Caption below the SVG.
toast_notification  — CSS slide-in/out fixed-position notification toast
  fields: title: string (optional). Bold notification title. Default "Changes saved"., message: string (optional). Body text. Default "Your updates have been applied successfully.", variant: "success" | "error" | "info" | "warning"  (optional, default "success"), position: "bottom-right" | "bottom-left" | "top-right" | "top-left"  (optional, default "bottom-right")
quiz_question  — MCQ or true/false question with CSS-only correct/wrong feedback
  fields: question: string. The question text., options: list[string]. Answer options — 2 to 6 items., correct: integer. Zero-based index of the correct option., explanation: string (optional). Shown after any option is selected., style: "default" | "dark" | "minimal"  (optional, default "default")
fill_in_blank  — cloze-test sentence with inline inputs and correct/wrong highlight on submit
  fields: template: string. Sentence with {blank} placeholders marking each gap., answers: list[string | list[string]]. Accepted answer(s) per blank in order. A list entry may itself be a list of acceptable alternatives., hint: string (optional). Shown below the exercise as a nudge., case_sensitive: boolean (optional, default false).
match_exercise  — click-to-pair matching exercise with green lock and red mismatch flash
  fields: pairs: list[{term: string, definition: string}]. 3 to 8 pairs recommended., shuffle: boolean (optional, default true). Randomise right-column order on render.
hint_reveal  — show/hide hint disclosure using HTML details/summary — no JS
  fields: hint: string. The hint text revealed on expand., label: string (optional). Button label. Default "Show hint"., accent: string (optional). Left-border and icon colour. Default "#6366f1".
achievement_badge  — unlockable achievement badge with locked/unlocked state and optional date
  fields: title: string. Achievement name., description: string (optional). Short achievement description., icon: string (optional). Emoji or single character used as the badge icon. Default "🏆"., locked: boolean (optional, default false). Shows greyscale padlock overlay when true., unlocked_at: string (optional). ISO date string shown beneath the badge when unlocked., color: string (optional). Badge accent colour. Default "#f59e0b"., size: "card" | "pill"  (optional, default "card")
score_summary  — end-of-exercise score card with correct/total, percentage, grade, and CTA
  fields: correct: integer. Number of correct answers., total: integer. Total number of questions., time_taken: string (optional). Human-readable time string e.g. "2m 14s"., pass_threshold: integer (optional). Percentage (0–100) required to pass. Drives pass/fail label colour., retry_label: string (optional). Label for the retry button. Omit to hide retry CTA., continue_label: string (optional). Label for the continue button. Omit to hide continue CTA., continue_url: url (optional). Destination for the continue button.
xp_bar  — animated XP/points progress bar with level label and level-up flash
  fields: level_label: string. Current level name e.g. "Level 3 — Intermediate"., xp_current: integer. Current XP within the current level., xp_next: integer. XP required to reach the next level., accent: string (optional). Bar fill colour. Default "#6366f1"., show_flash: boolean (optional, default true). Trigger level-up flash when xp_current >= xp_next.
lesson_nav  — prev/next lesson navigation with module context and optional completion checkbox
  fields: module_label: string (optional). Module or section name shown above the nav bar., current_title: string. Title of the current lesson., prev_title: string (optional). Title of the previous lesson. Omit to hide prev arrow., prev_url: url (optional). Link for the previous lesson., next_title: string (optional). Title of the next lesson. Omit to hide next arrow., next_url: url (optional). Link for the next lesson., show_completion: boolean (optional, default false). Show a "Mark as complete" checkbox persisted in localStorage.
course_progress_card  — course-level progress card with per-module bars and aggregate completion ring
  fields: course_title: string. Course name shown at the top of the card., modules: list[{title: string, lessons_total: integer, lessons_done: integer}]., accent: string (optional). Progress fill colour. Default "#6366f1".
highlighted_text  — highlighted text passage with optional hover margin annotation note
  fields: text: string. The passage to highlight., annotation: string (optional). Margin note revealed on hover., color: string (optional). Highlight background colour. Default "#fef08a" (yellow)., annotation_color: string (optional). Annotation pill background. Default "#fbbf24".
drive_file_list  — live list of Drive folder files
  fields: folder_id: string. The Google Drive folder ID to list files from., max_results: integer (optional). Maximum number of files to return. Default is 10.
sheet_preview  — live read-only Google Sheet range preview
  fields: spreadsheet_id: string. The Google Sheets ID., sheet_name: string. The name of the sheet tab., range: string. The A1 notation range (e.g. A1:D10).
gmail_summary  — list of recent Gmail messages matching query
  fields: query: string. The search query (e.g. "is:unread label:work")., max_results: integer (optional). Maximum number of emails to display. Default is 5.
calendar_upcoming  — list of upcoming calendar events
  fields: max_results: integer (optional). Maximum number of upcoming events to show. Default is 5.
user_greeting  — personalised greeting with active user email
  fields: prefix: string (optional). The greeting prefix. Default is "Hello".
script_run_button  — button to trigger server-side Apps Script function
  fields: label: string. The button text., function_name: string. The name of the server-side V8 JavaScript function to call., argument: string (optional). Optional string argument to pass to the function.
calendar_today  — today's calendar events from the user's default calendar
  fields: title: string (optional). Card heading. Default is "Today's Schedule"., max_results: integer (optional). Maximum events to show. Default 8.
sheet_stats  — aggregate stats from a sheet range displayed as stat badges
  fields: spreadsheet_id: string. The Google Sheets ID., sheet_name: string (optional). Sheet tab name., range: string. A1 notation range (e.g. B2:B50)., label: string (optional). Card heading. Default is "Sheet Stats"., show: array (optional). Which stats to show — any of sum, average, count, min, max. Default ["sum","average","count"]., accent: string (optional). Accent colour for stat values.
gmail_unread_count  — unread count badges for Gmail labels
  fields: labels: array (optional). Gmail label names to count. Default ["INBOX"]., title: string (optional). Card heading. Default is "Gmail"., accent: string (optional). Badge colour for non-zero counts. Default red., counts: object (static connector). Label→count map for non-GAS surfaces., auth_token: string (api connector). OAuth2 bearer token for REST API.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static); api(web|meet-stage,live)
user_profile_card  — user avatar, display name, email and domain — live on GAS, static fields elsewhere
  fields: name: string (static connector). Display name for non-GAS surfaces., email: string (static connector). Email address for non-GAS surfaces., accent: string (optional). Avatar background colour., subtitle: string (optional). Role or team label shown below the email.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static)
drive_storage_usage  — Drive storage quota progress bar — live on GAS, or pass used_gb/total_gb for static
  fields: label: string (optional). Card heading. Default is "Drive Storage"., accent: string (optional). Bar colour below 70% usage., used_gb: number (static connector). GB used — for non-GAS surfaces., total_gb: number (static connector). Total quota GB — for non-GAS surfaces., auth_token: string (api connector). OAuth2 bearer token for REST API.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static); api(web|meet-stage,live)
sheet_form_submit  — inline form that appends a row to a Google Sheet on submit
  fields: spreadsheet_id: string. Target Google Sheets ID., sheet_name: string (optional). Sheet tab name. Default is "Sheet1"., title: string (optional). Form heading., fields: array. Array of {label, name, type, placeholder} objects. type is text, email, number, or textarea., submit_label: string (optional). Submit button text. Default is "Submit"., accent: string (optional). Submit button colour.
tasks_today  — task checklist — live via Tasks API on GAS, items[] array on other surfaces
  fields: title: string (optional). Card heading. Default is "Today's Tasks"., max_results: integer (optional). Maximum tasks to show. Default 10., list_name: string (optional, gas-native). Name of the task list., items: array (static connector). Array of {title, due, completed} for non-GAS surfaces., auth_token: string (api connector). OAuth2 bearer token for REST API.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static); api(web|meet-stage,live)
cursor_glow  — ambient glowing orb that lerp-follows the cursor with screen blend
  fields: colour: string (optional). Orb colour. Default, size: integer (optional). Orb diameter in px. Default 380., opacity: number (optional). Orb opacity 0–1. Default 0.18., speed: number (optional). Lerp factor 0–1 — lower = more lag. Default 0.1., blend: string (optional). CSS mix-blend-mode. Default screen.
cursor_trail  — chain of fading dots following the cursor with worm physics
  fields: colour: string (optional). Dot colour. Default, length: integer (optional). Number of chain dots. Default 16., size: integer (optional). Lead dot diameter px. Default 10., speed: number (optional). Lerp factor per dot. Default 0.35.
particle_burst  — click anywhere to burst coloured gravity particles from click point
  fields: count: integer (optional). Particles per click. Default 14., colours: array (optional). Array of hex colour strings., size: integer (optional). Particle diameter px. Default 8., duration: integer (optional). Animation duration ms. Default 700., gravity: number (optional). Downward pull factor. Default 1.2.
spotlight_cursor  — dark overlay with cursor-following circular cutout — torch effect
  fields: radius: integer (optional). Spotlight radius px. Default 180., darkness: number (optional). Overlay opacity 0–1. Default 0.82., colour: string (optional). Overlay colour. Default, soft_edge: integer (optional). Feather distance px beyond radius. Default 60.
magnetic_element  — content that drifts toward cursor and springs back with overshoot
  fields: label: string (optional). Text label for the default pill style., content: string (optional). Raw HTML to use instead of the default pill., accent: string (optional). Pill background colour. Default, radius: integer (optional). Activation distance px. Default 120., strength: number (optional). Pull factor 0–1. Default 0.4.
tilt_card  — 3D perspective tilt card with glare highlight driven by cursor position
  fields: content: string (optional). Inner HTML rendered inside the card., title: string (optional). Card heading rendered above content., max_tilt: number (optional). Maximum rotation degrees. Default 14., glare: boolean (optional). Show glare highlight. Default true., accent: string (optional). Glare colour. Default rgba(255,255,255,0.15)., padding: string (optional). Inner padding. Default 28px.
doc_ai_summary  — AI-powered Google Doc summary via Vertex AI Gemini
  fields: doc_id: string. Google Doc ID to summarise., prompt: string (optional). Instruction sent to Gemini before the doc text., title: string (optional). Override card title. Defaults to the doc name., model: string (optional). Gemini model override. Defaults to VERTEX_MODEL property., max_chars: integer (optional). Max doc characters sent to Gemini. Default 12000., accent: string (optional). Accent colour., show_meta: boolean (optional). Show word count and doc link. Default true.
multi_doc_ai_brief  — multi-doc briefing pack — one Gemini summary card per Google Doc
  fields: docs: array. Array of {doc_id, title?, prompt?} objects., default_prompt: string (optional). Fallback prompt for docs without their own., accent: string (optional). Accent colour for doc links., model: string (optional). Gemini model override.
gradient_heading  — gradient-fill standalone heading
  fields: text: string. Heading text., gradient: string (optional). CSS gradient value. Default indigo→violet→pink., size: string (optional). Font-size. Default clamp(1.8rem,4vw,3rem)., weight: integer (optional). Font-weight. Default 900., align: string (optional). text-align. Default left., margin: string (optional). CSS margin. Default 16px 0 6px.
display_quote  — typographic pull quote with decorative mark and attribution
  fields: text: string. Quote body text., attribution: string (optional). Name or source shown below quote., colour: string (optional). Accent colour for mark and attribution. Default, size: string (optional). Font-size for quote text. Default clamp(1.4rem,3vw,2.2rem)., align: string (optional). center or left. Default center.
split_stat  — two-column stat + text keynote layout with neon glow
  fields: value: string. The stat number or short value., prefix: string (optional). Text before value (e.g. "$", "~")., suffix: string (optional). Text after value (e.g. "%", "k", "+")., heading: string (optional). Right-side heading., body: string (optional). Right-side paragraph text., colour: string (optional). Stat glow colour. Default, flip: boolean (optional). Put stat on right side. Default false.
word_reveal  — auto-play word-by-word fade-up reveal animation
  fields: text: string. Text to reveal word by word., colour: string (optional). Text colour. Default rgba(255,255,255,0.92)., gradient: string (optional). CSS gradient applied to whole line (overrides colour)., size: string (optional). Font-size. Default clamp(2rem,5vw,3.5rem)., weight: integer (optional). Font-weight. Default 800., delay: number (optional). Seconds between each word. Default 0.12., align: string (optional). text-align. Default center.
section_label  — uppercase section marker with glowing accent pill
  fields: text: string. Label text (uppercased automatically)., colour: string (optional). Accent colour. Default, margin: string (optional). Vertical margin. Default 24px 0 12px.
count_up_stat  — animated count-up number stat with cubic ease, auto-plays on load
  fields: value: integer. Target number to count to., label: string (optional). Descriptor shown below the number., prefix: string (optional). Text before the number (e.g. "$")., suffix: string (optional). Text after the number (e.g. "%", "k")., colour: string (optional). Glow colour. Default, duration: integer (optional). Count-up duration ms. Default 1800., size: string (optional). Font-size. Default 4rem.
text_highlight  — prose sentence with **marked** words highlighted in accent colour
  fields: text: string. Body text with **highlighted** words wrapped in double asterisks., size: string (optional). Font-size. Default 1.2rem., colour: string (optional). Highlight colour. Default, weight: integer (optional). Base font weight. Default 600., align: string (optional). text-align. Default left.
reveal_line  — clip-path sweep-in reveal line, auto-plays on load
  fields: text: string. Text content., gradient: string (optional). CSS gradient applied to text. Default indigo→pink., size: string (optional). Font-size. Default clamp(2.5rem,6vw,4rem)., weight: integer (optional). Font-weight. Default 900., duration: integer (optional). Animation duration ms. Default 800., delay: integer (optional). Start delay ms. Default 200.
canvas_plexus  — animated particle plexus with proximity lines and mouse repulsion
  fields: count: integer (optional). Number of particles. Default 65., colour: string (optional). Hex colour for particles and lines. Default, speed: number (optional). Particle speed multiplier. Default 1.0., max_dist: integer (optional). Max distance px for edge connections. Default 120., bg: string (optional). Background colour. Default, height: integer (optional). Canvas height px. Default 400., repulse_radius: integer (optional). Mouse repulsion radius px. Default 90.
spring_nodes  — interactive mass-spring physics graph with drag-to-pin nodes
  fields: nodes: array (optional). Array of {id, label} objects. Defaults to 6 labelled nodes., edges: array (optional). Array of {a, b} index pairs for spring connections., colour: string (optional). Node and edge accent colour. Default, bg: string (optional). Background colour. Default, height: integer (optional). Canvas height px. Default 420., rest_length: integer (optional). Spring rest length px. Default 110.
isometric_mesh  — rotating 3D isometric mesh with height-colour mapping and drag-rotate
  fields: grid: integer (optional). Grid dimension N (N×N). Default 16., height_scale: number (optional). Vertical exaggeration multiplier. Default 1.0., colour_low: string (optional). Hex colour at minimum height. Default, colour_high: string (optional). Hex colour at maximum height. Default, bg: string (optional). Background colour. Default, height: integer (optional). Canvas height px. Default 460., auto_rotate: boolean (optional). Auto-rotate until user drags. Default true.
geo_iso_takeoff  — isometric 3D canvas of A321neo takeoff from LFBO — animated roll, rotation, gear-up, climb; HUD with airline/runway
  fields: title: string (optional). HUD title line. Default "LFBO RWY 32L — A321neo DEPARTURE"., airline: string (optional). ICAO airline code for accent colour — AIB, EZY, AFR, BAW, DLH, RYR. Default AIB., aircraft_type: string (optional). ICAO aircraft type code — A21N (A321neo), A320, B738. Default A21N.
geo_iso_rocket_launch  — isometric 3D canvas of Ariane 6 rocket launch from Kourou — animated liftoff and ascent; mission HUD
  fields: title: string (optional). HUD title. Default "KOUROU ELA-4 — HEAVY LIFT INJECTION PROFILE"., vehicle: string (optional). ARIANE_6 or ARIANE_5. Default ARIANE_6.
geo_iso_heli_hover  — isometric 3D canvas of H160 helicopter hover — rotor animation, downwash, HUD
  fields: title: string (optional). HUD title. Default "LFBO HELIPAD 2 — AIRBUS H160 HOVER PROFILE"., livery: string (optional). ICAO airline code for accent colour — AIB, EZY, AFR, etc. Default AIB.
geo_iso_fleet  — tabbed isometric fleet demo — A321neo takeoff + Ariane 6 launch + H160 hover with tab switcher
  fields: airline: string (optional). Airline ICAO for A321neo accent — AIB, EZY, AFR, BAW, DLH, RYR. Default AIB., rocket: string (optional). ESA or CNES. Default ESA., livery: string (optional). Airline ICAO for H160 livery. Default AIB., tab: string (optional). Starting tab — "ac" (A321neo), "rk" (Ariane 6), "hh" (H160). Default ac.
airspace_command_deck  — Toulouse TMA radar canvas with animated flights, HUD overlay, and live METAR ticker
  fields: chyron_title: string (optional). Top-left headline overlay., chyron_subtitle: string (optional). Top-left subtitle — supports interpolated METAR tags., ticker_text: string (optional). Scrolling bottom bar text., ticker_speed: integer (optional). Ticker scroll speed px/s. Default 45., panel_type: string (optional). supervisor | target | (empty). Controls HUD flight list panel., panel_title: string (optional). HUD panel heading., lockedCallsign: string (optional). Highlight and add targeting reticle to this callsign., zoom: integer (optional). TMA radius shown in nm. Default 35., height: integer (optional). Canvas height px. Default 520., show_slate: boolean (optional). Render calibration boot slate instead of radar., slate_title: string (optional). Slate heading., slate_description: string (optional). Slate body text., poll_question: string (optional). If set, renders a vote overlay with bar chart., poll_options: array (optional). Array of option strings for the poll., poll_values: array (optional). Array of integer vote counts for each option.
data_source  — generic HTTP feed — server-side initial fetch, client-side refresh via surface transport
  fields: name: string. Feed identifier — other atoms subscribe to this name (required)., url: string. HTTP GET endpoint., format: string (optional). json | text. Default json., path: string (optional). Dot-notation path into parsed response (e.g. data.items)., refresh: integer (optional). Client refresh interval seconds. 0 = initial load only. Default 0., cache: integer (optional). Server-side CacheService TTL seconds. Default 15.
adsb_feed  — OpenSky Network ADS-B live flight positions for a bounding box
  fields: name: string (optional). Feed name other atoms subscribe to. Default adsb., lat_min: number (optional). Bounding box south edge degrees. Default 43.1 (LFBO TMA)., lat_max: number (optional). Bounding box north edge degrees. Default 44.2., lon_min: number (optional). Bounding box west edge degrees. Default 0.7., lon_max: number (optional). Bounding box east edge degrees. Default 2.0., refresh: integer (optional). Client refresh interval seconds. Default 15., filter_ground: boolean (optional). Exclude on-ground traffic. Default true., cache: integer (optional). Server-side cache TTL seconds. Default 15.
metar_feed  — live METAR weather feed — parsed wind, temp, QNH for an ICAO station
  fields: name: string (optional). Feed name other atoms subscribe to. Default metar., station: string (optional). ICAO station code. Default LFBO., refresh: integer (optional). Client refresh interval seconds. Default 60., cache: integer (optional). Server-side cache TTL seconds. Default 30.
paragraph  — prose paragraph (GAS alias for body)
  fields: text: string
text_block  — plain text block
  fields: text: string
blockquote  — styled pull-quote with attribution
  fields: text: string, attribution: string (optional)
spacer  — vertical whitespace gap
  fields: height: string or number (optional, CSS height e.g. 24 or "2rem")
tag_chip  — inline tag chip
  fields: text: string, color: string (optional, hex colour)
badge  — inline badge pill
  fields: text: string, color: string (optional, hex colour)
inline_code  — monospace inline code span
  fields: text: string
code_block  — syntax-highlighted code block
  fields: language: string (optional, e.g. python, js, yaml), content: string
link_button  — text hyperlink button
  fields: url: string, label: string
cta_button  — call-to-action button
  fields: url: string, label: string, color: string (optional, hex)
nav_link  — navigation link
  fields: url: string, label: string
info_card  — simple info card with title and body
  fields: title: string, text: string
ai_build_trace  — Gemini token usage trace card
  fields: model: string (optional, e.g. gemini-2.5-flash), prompt_tokens: integer (optional), thinking_tokens: integer (optional), output_tokens: integer (optional), total_tokens: integer (optional)
gemini_prompt  — inline Gemini prompt input widget
  fields: label: string (optional), placeholder: string (optional), accent: string (optional, hex colour)
dark_hero  — dark hero banner with gradient and CTA
  fields: heading: string, subtext: string (optional), badge: string (optional, small label above heading), gradient: string (optional, CSS gradient e.g. linear-gradient(135deg,#1e1b4b,#312e81)), cta_label: string (optional), cta_url: string (optional), align: string (optional, left|center)
glowing_stat  — neon-glow stat number on dark card
  fields: value: string or number, label: string (optional), colour: string (optional, hex, default #22d3ee), size: string (optional, CSS font-size), prefix: string (optional), suffix: string (optional), glow: boolean (optional)
glass_card  — frosted-glass card on gradient background
  fields: title: string (optional), text: string (optional, supports markdown), bg: string (optional, CSS gradient or colour for the outer container)
gradient_border_card  — animated gradient border card
  fields: title: string (optional), content: string (optional), colours: array of hex strings (optional, gradient stops), bg: string (optional, card background), angle: number (optional, gradient angle degrees), padding: string (optional), radius: string (optional)
floating_orbs  — decorative blurred colour orbs background
  fields: orbs: array of {colour, size, x, y} (optional), blur: number (optional, blur px), opacity: number (optional, 0–1), animate: boolean (optional)
neon_text  — neon-glow coloured text
  fields: text: string, colour: string (optional, hex, default #22d3ee), size: string (optional, CSS font-size), weight: string or number (optional), align: string (optional, left|center|right), flicker: boolean (optional)
dark_feature_grid  — dark-theme feature grid with icons
  fields: features: array of {icon, title, description, colour}, columns: integer (optional, default 3), accent: string (optional, hex)
dark_divider  — dark-theme horizontal divider
  fields: colour: string (optional, hex), margin: string (optional, CSS margin), height: string (optional, CSS height)
ambient_gradient  — animated aurora/ambient gradient background
  fields: title: string (optional), text: string (optional)
depth_stack  — stacked cards with depth parallax
  fields: cards: array of {title, text} (alias: items), count: integer (optional, max cards to show)
scramble_reveal  — character-scramble text reveal on scroll
  fields: text: string (alias: content, label), title: string (optional)
scroll_trigger  — scroll-triggered animated reveal
  fields: text: string (alias: content), title: string (optional), delay: number (optional, seconds), direction: string (optional, up|down|left|right)
flow_connector  — animated beam connector between two nodes
  fields: from: string, to: string, label: string (optional), color: string (optional, hex)
live_metric  — animated counting number (alias for animated_counter)
  fields: value: number (alias: end), start: number (optional), duration: number (optional, seconds), prefix: string (optional), suffix: string (optional), label: string (optional), decimals: integer (optional)
deadline_ticker  — countdown timer to a target date (alias)
  fields: target_date: string (ISO date, alias: target), label: string (optional, alias: title)
pattern_background  — dot-grid pattern background (alias)
  fields: color: string (optional, dot colour hex), bg: string (optional, background colour), size: number (optional, dot spacing px), title: string (optional), text: string (optional)
glitch_text  — RGB-split glitch-effect headline
  fields: text: string (alias: title, label), size: string (optional, CSS font-size, default 2rem)
neon_glow  — pulsing neon-glow text on dark card
  fields: text: string (alias: title, label), color: string (optional, hex, default #22d3ee), size: string (optional, CSS font-size)
magnetic_button  — magnetic cursor-following button
  fields: text: string (alias: label, title), color: string (optional, hex background)
confetti_burst  — auto-fire confetti achievement card
  fields: label: string (alias: text, title, default "Achievement Unlocked!")
confetti_trigger  — click-to-trigger confetti button
  fields: label: string (message shown after click, alias: text), trigger: string (button label, alias: button)
floating_particles  — floating particles background (canvas placeholder)
  fields: title: string (optional, alias: label, text)
parallax_section  — parallax scroll section (canvas placeholder)
  fields: title: string (optional, alias: label, text)
scroll_progress  — fixed scroll-progress bar at page top
  fields: color: string (optional, hex, default #6366f1), height: number (optional, px, default 3)
live_clock  — live ticking clock widget
  fields: label: string (optional, alias: title), format: string (optional, 12h|24h, default 24h), timezone: string (optional, IANA tz label for display only)
decision_tree  — interactive collapsible decision tree
  fields: nodes: array of {text, children: [{text, children}]} — nested tree nodes, title: string (optional)
step_reveal_sequence  — tabbed step-by-step sequence
  fields: steps: array of {title, text} — each step shown in its own tab panel
chat_sequence  — animated chat conversation thread
  fields: messages: array of {role (user|assistant), name (optional), text}
tooltip_glossary  — glossary with hover tooltips
  fields: terms: array of {term, definition}, text: string (optional, introductory prose, alias: intro)
focus_lens  — spotlight focus lens on blurred background
  fields: title: string (optional), text: string (optional, alias: content)
terminal_boot  — animated terminal boot sequence
  fields: lines: array of strings — lines typed out in sequence, title: string (optional, shown as terminal header), speed: number (optional, ms between lines, default 380)
stagger_list  — stagger-animated list of items
  fields: items: array of strings or {icon, text, sub} objects, direction: string (optional, up|down|left|right), stagger: number (optional, delay between items in seconds, default 0.1)
liquid_button  — liquid morphing hover button
  fields: text: string (alias: label, title), color: string (optional, hex background)
highlight_sweep  — animated highlight sweep text
  fields: text: string (alias: content), color: string (optional, highlight colour hex, default #fef08a yellow), delay: number (optional, seconds before sweep starts), size: string (optional, CSS font-size)
progress_reveal  — scroll-triggered animated progress bar
  fields: value: number (0–100, alias: percent), label: string (optional, alias: title), color: string (optional, hex), suffix: string (optional, default %), height: number (optional, bar height px)
big_reveal  — spring-animation big number or word reveal
  fields: text: string (the big value, alias: value, label), sub: string (optional subtitle below, alias: subtitle), color: string (optional, hex), size: string (optional, CSS font-size, default 5rem), delay: number (optional, seconds)
kinetic_headline  — word-by-word kinetic headline animation
  fields: text: string (alias: title), size: string (optional, CSS font-size), color: string (optional, hex), stagger: number (optional, seconds between words), style: string (optional, up|down|scale|fade)
text_reveal_mask  — clip-path text reveal mask animation
  fields: text: string (alias: title), size: string (optional, CSS font-size), color: string (optional, hex), delay: number (optional, seconds)
split_reveal  — split-panel reveal animation
  fields: title: string (optional), text: string (optional, alias: content), color: string (optional, panel colour hex), delay: number (optional, seconds)
mesh_gradient  — dark card with radial mesh gradient background
  fields: title: string (optional), text: string (optional, alias: content), bg: string (optional, base background colour), colors: array of hex strings (optional, gradient blob colours)
stripe_background  — animated diagonal stripe background card
  fields: title: string (optional), text: string (optional, alias: content), color1: string (optional, hex, first stripe colour), color2: string (optional, hex, second stripe colour), speed: number (optional, animation seconds)
status_timeline  — status-dot vertical timeline
  fields: events: array of {title, date (optional), text (optional), status (done|active|pending|error|warning)}, title: string (optional)
counter_group  — row of animated stat counters
  fields: stats: array of {value, label, color (optional), prefix (optional), suffix (optional), decimals (optional)} (alias: items)
orbit_diagram  — animated orbit diagram with satellite nodes
  fields: center: string (label for the central node), nodes: array of strings or {label, color} objects, color: string (optional, hex accent), speed: number (optional, animation speed)
noise_card  — dark card with film-grain noise texture
  fields: title: string (optional), text: string (optional, alias: content), bg: string (optional, background colour), color: string (optional, text colour)
comparison_morph  — draggable before/after comparison slider
  fields: before: {label (optional), text}, after: {label (optional), text}, title: string (optional)
word_cloud  — interactive word cloud with optional live Sheet feed
  fields: words: array of {text, weight} (optional static words), palette: array of hex strings (optional, word colours), placeholder: string (optional, input placeholder), accent: string (optional, hex accent for input bar), sheet_url: string (optional, Google Sheet CSV URL for live words), write_url: string (optional, GAS doGet URL to write submissions), poll: number (optional, poll interval seconds)
quiz_set  — multi-question interactive quiz
  fields: title: string (optional), questions: array of {question, options: [string], correct: integer (0-based index), explanation (optional)}, pass_score: integer (optional, % to pass, default 70), accent: string (optional, hex), on_pass: object (optional, atom block shown on pass), on_fail: object (optional, atom block shown on fail)
globe_3d  — interactive spinning 3-D globe (wire or earth)
  fields: size: number (optional, diameter px, default 300), color: string (optional, hex accent, default #6366f1), speed: number (optional, auto-spin speed, default 0.006), lines: number (optional, latitude line count, default 10), theme: string (optional, wire|earth, default wire), dots: array of {lat, lon, label (optional), color (optional)} (optional, pins on globe), arcs: array of {from: [lat,lon], to: [lat,lon], color (optional)} (optional, great-circle arcs)
geo_mercator_radar  — dark-theme interactive Mercator map with node pins and links
  fields: title: string (optional), color: string (optional, hex accent, default #00f2ff), height: number (optional, px, default 450), nodes: array of {id, name, lat, lon, value (optional)}, links: array of {from: id, to: id} (optional)
geo_contour_waves  — animated atmospheric contour wave field
  fields: title: string (optional), color: string (optional, hex, default #a78bfa), intensity: number (optional, wave band count, default 4, max 8), height: number (optional, px, default 350)
multi_surface  — three-engine multi-surface demo atom
  fields: title: string (optional), nodes: array of {id, type, label, temp (optional), value (optional), intensity (0–100, optional), coords: {x, y}}
geo_europe_airspace  — interactive European airspace map with airports and flights
  fields: title: string (optional), focus: string (optional, country name to highlight, alias: country), sim_flights: array of {callsign, from: [lat,lon], to: [lat,lon]} (optional simulated flight tracks), airports: boolean (optional, show airport pins, default true)
feed_status  — live/sim status pill for a named data feed
  fields: name: string (feed name to subscribe to), label: string (optional, text prefix in pill), size: string (optional, CSS font-size, default 0.6rem)
playbook  — multi-slide fullscreen presentation playbook
  fields: slides: array of {id (optional), blocks: [atom block objects]} — each slide is a full block list, shared_blocks: array of atom block objects (optional, data feeds etc. rendered once), transition: string (optional, fade|slide, default fade)
surface_unlocked  — achievement-style surface unlocked notification
  fields: icon: string (optional, emoji, default ⚡), surface: string (surface/feature name displayed large), sub: string (optional, subtitle, default NEW SURFACE UNLOCKED), accent: string (optional, hex)
schema_reveal  — self-reveal: shows this page's own JSON schema
  fields: title: string (optional), accent: string (optional, hex)
url_anatomy  — annotated URL anatomy diagram
  fields: accent: string (optional, hex)
schema_qr  — QR code for current or given URL
  fields: url: string (optional, fixed URL — defaults to current page URL), label: string (optional), sub: string (optional, sub-label below QR), size: number (optional, px, default 220)
take_away_card  — bold screenshot-ready insight card
  fields: headline: string (alias: text, quote, insight), sub: string (optional, attribution/source, alias: author, source), accent: string (optional, hex), size: string (optional, CSS font-size), gradient: array of 2 hex strings (optional, background gradient colours)
next_step_strip  — horizontal numbered next-steps strip
  fields: steps: array of {number (optional), label, detail (optional, alias: action), url (optional)}, accent: string (optional, hex)
copy_prompt  — copyable monospace prompt/code block
  fields: prompt: string (text to display and copy, alias: text, content), label: string (optional, header label), accent: string (optional, hex)
atom_anatomy  — rendered atom + raw schema side-by-side anatomy view
  fields: label: string (optional, panel header), schema: object (atom block JSON to render and display), accent: string (optional, hex)
renderer_stats  — stat grid for renderer capability metrics
  fields: stats: array of {value, label}, sub: string (optional, footer note), accent: string (optional, hex)
prompt_to_schema  — three-panel prompt → schema → output flow
  fields: prompt: string (the input prompt text), schema: object or string (the generated JSON schema), output: string (description of the rendered output), labels: array of 3 strings (optional, panel headers), accent: string (optional, hex)
before_after_stack  — old-vs-new stack comparison animation
  fields: items: array of strings (old approach items to cross out, alias: before_items), before_label: string (optional), after_label: string (optional), result: string (the new approach shown after animation, alias: after_text), delay: number (optional, seconds between strikes), accent: string (optional, hex)
live_vote  — live audience voting with real-time bar chart results
  fields: question: string, options: array of strings (vote choices), sheet_url: string (optional, Google Sheet CSV for live tallies), write_url: string (optional, GAS doGet URL to record votes), poll: number (optional, poll interval ms, default 5000), accent: string (optional, hex)
reaction_shower  — emoji reaction buttons with raining particles
  fields: reactions: array of emoji strings (optional, default 🔥💡🤯👏), write_url: string (optional, GAS doGet URL to record reactions), sheet_url: string (optional, Google Sheet CSV for live counts), poll: number (optional, poll interval ms), accent: string (optional, hex)
raise_hand  — raise-hand button with live participant count
  fields: question: string (optional, prompt text above button), label: string (optional, button label, default ✋ Raise hand), write_url: string (optional, GAS doGet URL to record hands), sheet_url: string (optional, Google Sheet CSV for live count), poll: number (optional, poll interval ms), accent: string (optional, hex)
surface_map  — A2UI surface diagram (schema → surfaces)
  fields: title: string (optional), surfaces: array of {name, icon, desc, color} (optional, defaults to GAS/Meet/Sites/Chat), accent: string (optional, hex)
speed_counter  — live page-load stopwatch
  fields: label: string (optional, e.g. "Page loaded in"), sub: string (optional, sub-label), accent: string (optional, hex)
live_edit  — embedded live atom JSON editor with preview
  fields: placeholder: string (optional, example atom JSON), accent: string (optional, hex), renderer_url: string (optional, renderer base URL for linking)
globe_3d  — rotating 3D wireframe globe canvas with configurable size, colour, speed, and grid lines
  fields: size: integer (optional). Canvas width/height in px. Default 300., color: string (optional). Line colour hex. Default, speed: number (optional). Rotation speed radians/frame. Default 0.006., lines: integer (optional). Number of latitude/longitude lines. Default 10.
glass_card  — frosted-glass card with blur backdrop — dark-theme highlight box
  fields: title: string (optional). Card heading text., content: string (optional). Inner HTML content of the card., blur: integer (optional). Backdrop blur in px. Default 18., bg: string (optional). Background colour (rgba). Default rgba(255,255,255,0.05)., border: string (optional). Border colour (rgba). Default rgba(255,255,255,0.1)., padding: string (optional). CSS padding. Default 28px., radius: string (optional). Border radius. Default 16px.
tilt_card  — 3D gyroscopic tilt card with cursor-tracking perspective and optional glare
  fields: title: string (optional). Card heading., content: string (optional). Inner HTML content., max_tilt: integer (optional). Maximum tilt angle in degrees. Default 14., glare: boolean (optional). Show glare highlight. Default true., accent: string (optional). Glare/accent colour. Default rgba(255,255,255,0.15)., padding: string (optional). CSS padding. Default 28px.
cursor_glow  — ambient cursor-following radial glow overlay — cinematic dark-page effect
  fields: colour: string (optional). Glow colour hex. Default, size: integer (optional). Glow diameter in px. Default 380., opacity: number (optional). Glow opacity 0–1. Default 0.18., speed: number (optional). Follow speed 0–1 (lerp factor). Default 0.1., blend: string (optional). CSS mix-blend-mode. Default screen.
youtube  — YouTube video link card (GAS sandbox — renders as watch-on-YouTube button)
  fields: url: string (required). Full YouTube watch URL e.g. https://www.youtube.com/watch?v=VIDEO_ID., title: string (optional). Card label shown above the link.
embed_codepen  — CodePen embed — degrades to link card in GAS
  fields: url: string (required). CodePen pen URL.
embed_stackblitz  — StackBlitz embed — degrades to link card in GAS
  fields: url: string (required). StackBlitz project URL.
embed_gist  — GitHub Gist embed — degrades to link card in GAS
  fields: url: string (required). GitHub Gist URL.
embed_google_slides  — Google Slides embed — degrades to link card in GAS
  fields: url: string (required). Google Slides share URL.
figma_embed  — Figma embed — degrades to link card in GAS
  fields: url: string (required). Figma file or prototype URL.
lottie_animation  — Lottie animation — degrades to static fallback image in GAS
  fields: fallback_image_url: string (optional). Static image URL shown in GAS instead of the animation., caption: string (optional). Caption below the fallback image.
parallax_card  — parallax card — degrades to static title/subtitle card in GAS
  fields: title: string (optional). Card heading., subtitle: string (optional). Card subtext.
embed_tweet  — static tweet quote blockquote with author attribution — no external JS needed
  fields: text: string (required). Tweet text content., author: string (optional). Twitter handle or display name shown as citation.
social_feed_embed  — social feed embed — degrades to link card in GAS
  fields: url: string (required). Social media profile or feed URL.
live_demo_embed  — live demo embed — degrades to link card with Open Demo button in GAS
  fields: title: string (optional). Demo title shown in card header., url: string (required). Demo URL to open in new tab., note: string (optional). Explanatory note shown in the card body.
gmail_inbox  — swipeable Gmail inbox carousel — live on GAS, items[] or api connector on web/meet
  fields: title: string (optional). Section label above carousel. Default "Inbox"., count: integer (optional). Number of threads, max 20. Default 10., accent: string (optional). Accent colour for unread indicator and nav dot. Default, items: array (static connector). Email objects for non-GAS surfaces., auth_token: string (api connector). OAuth2 bearer token for REST API.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static); api(web|meet-stage,live)
drive_recent_files  — swipeable Drive files carousel — live on GAS, items[] or api connector on web/meet
  fields: title: string (optional). Section label above carousel. Default "Recent Files"., count: integer (optional). Number of files to show, max 20. Default 10., accent: string (optional). Accent colour for active nav dot. Default, items: array (static connector). File objects for non-GAS surfaces., auth_token: string (api connector). OAuth2 bearer token for REST API.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static); api(web|meet-stage,live)
drive_folder_contents  — Drive folder grid — live on GAS via folder_id, items[] or api connector on web/meet
  fields: folder_id: string (gas-native/api). The Google Drive folder ID to browse., title: string (optional). Override for the folder name shown as header., count: integer (optional). Max items to show. Default 12., items: array (static connector). File objects for non-GAS surfaces., auth_token: string (api connector). OAuth2 bearer token for REST API.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static); api(web|meet-stage,live)
drive_file_card  — single Drive file card — static on all surfaces; live name/type lookup via file_id on GAS
  fields: file_id: string (gas-native). Drive file ID for live name/type lookup on GAS., name: string. File display name — required on non-GAS surfaces., mime: string. MIME type for badge colour (e.g. application/vnd.google-apps.spreadsheet)., url: string. URL to open — required on non-GAS surfaces., description: string (optional). Short description shown below the file name.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static)
progress_store  — invisible LMS state connector — Sheet on GAS, localStorage on web; exposes window._A2UI_STORE
  fields: course_id: string (required). Unique course identifier — scopes the Sheet and localStorage key.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static)
module_map  — course curriculum grid — module cards with live locked/available/complete status from progress_store
  fields: title: string (optional). Section heading. Default "Course Modules"., columns: integer (optional). Grid columns, max 4. Default 3., modules: array (required). Array of module objects. Each module supports: id (string, required), title, description, icon, duration, lessons, required[] (array of module ids that must be complete to unlock), and either: page (array of atom blocks, PREFERRED — auto-encoded into a self-contained URL at render time, no separate save needed) or url (string — only for external URLs or pre-saved nav pages). Always use page for inline module content.
knowledge_check  — inline comprehension pulse — single question, instant feedback, no score pressure
  fields: question: string (required). The comprehension question., options: array (required). Array of answer strings., correct: integer (required). Zero-based index of the correct answer., explanation: string (optional). Explanation shown after any selection.
quiz_result_summary  — end-of-quiz result — score %, pass/fail, question dots, writes to progress_store
  fields: score: integer (required). Number of correct answers., total: integer (required). Total number of questions., quiz_id: string (required). ID used to write score to progress_store., pass_mark: integer (optional). Percentage required to pass. Default 70., time_secs: integer (optional). Time taken in seconds for display., questions: array (optional). Array of {label, correct} for per-question breakdown dots., next_url: string (optional). URL for Continue button (shown when passed)., retry_url: string (optional). URL for Retry button.
scenario_branch  — branching scenario — situation + choices + consequence reveal with good/neutral/bad outcome
  fields: scenario: string (required). The situation or challenge presented to the learner., context: string (optional). Background context shown in italics above the scenario., accent: string (optional). Accent colour for choice buttons. Default, choices: array (required). Array of {label, consequence, outcome, next_url?} objects. outcome is "good", "neutral", or "bad".
completion_gate  — content lock — hides until requires module id is complete in progress_store
  fields: requires: string (required). Module id that must be complete in progress_store to unlock., label: string (optional). Lock card heading. Default "Locked"., message: string (optional). Message shown on the lock card.
certification_card  — completion certificate — locked until requires id complete in progress_store; earner from GAS session
  fields: course: string (required). Course name on the certificate., issuer: string (optional). Issuing organisation name. Default "A2UI Learning"., requires: string (optional). Module/course id that must be complete to reveal the certificate., earner: string (optional). Earner display name — auto-derived from GAS session if not set., date: string (optional). Completion date string. Defaults to today., accent: string (optional). Gradient accent colour. Default
skill_radar  — SVG radar/spider chart of skill competency levels — optional before/after growth overlay
  fields: title: string (optional). Chart heading. Default "Skill Profile"., accent: string (optional). Fill/stroke colour for current polygon. Default, skills: array (required). Array of {label, value (0-100), before? (0-100)} objects.
badge_showcase  — achievement badge wall — earned badges glow, locked badges grey; status from progress_store
  fields: title: string (optional). Section heading. Default "Achievements"., columns: integer (optional). Grid columns, max 6. Default 4., badges: array (required). Array of {id, label, icon, description, required_id} objects. required_id is the progress_store key to check for completion.
learning_path_selector  — course entry path chooser — role/level cards, writes selection to progress_store, optional navigation
  fields: title: string (optional). Chooser heading. Default "Choose Your Path"., intro: string (optional). Introductory text below the heading., paths: array (required). Array of {id, label, description, icon, accent, duration, url?} objects.
video_checkpoint  — YouTube video with pausing quiz checkpoints — learner must answer to continue
  fields: youtube_id: string (required). YouTube video ID., title: string (optional). Section heading above the player., checkpoints: array (required). Array of {at_seconds, question, options[], correct (0-based index), explanation} objects.
cohort_progress_board  — instructor cohort table — per-learner module completion + scores; live on GAS
  fields: course_id: string (required). Matches the progress_store course_id., title: string (optional). Board heading. Default "Cohort Progress"., modules: array (optional). Array of {id, label} for column headers. Drives per-module completion dots., items: array (optional, web/static). Array of {email, progress{}, updated_at} learner objects.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static)
reflection_prompt  — reflection textarea — saves to progress_store; restores on revisit
  fields: prompt: string (required). The reflection question shown above the textarea., prompt_id: string (optional). Key suffix for progress_store. Default "reflection"., placeholder: string (optional). Textarea placeholder text., accent: string (optional). Accent colour. Default
annotation_highlight  — annotated body text — click highlighted terms to reveal inline explanations
  fields: text: string (required). Body text passage. Annotated terms are replaced server-side., notes: array (required). Array of {term, explanation, color?} objects. First match in text is highlighted.
onboarding_stepper  — guided onboarding steps — completes to progress_store, restores on revisit
  fields: title: string (optional). Stepper heading. Default "Get Started"., accent: string (optional). Active step indicator colour. Default, steps: array (required). Array of {id, icon, label, description, action_label, action_url?} objects.
case_study_card  — structured case study — situation, data points, questions, optional model answer reveal
  fields: title: string (required). Case study title., situation: string (required). The scenario narrative., data_points: array (optional). Array of {label, value, note?} metric blocks., questions: array (optional). Array of question strings for analysis., model_answer: string (optional). Model answer text shown on toggle. Hidden by default., accent: string (optional). Accent colour for data point values. Default
study_timer  — Pomodoro focus/break timer with SVG ring — session only, no persistence
  fields: label: string (optional). Timer heading. Default "Study Timer"., focus_mins: integer (optional). Focus period in minutes. Default 25., break_mins: integer (optional). Break period in minutes. Default 5., accent: string (optional). Ring and mode label colour. Default
rubric_card  — assessment rubric table — criteria rows × performance level columns
  fields: title: string (optional). Table heading. Default "Assessment Rubric"., levels: array (optional). Performance level column headers. Default [Beginning, Developing, Proficient, Exemplary]., accent: string (optional). Highest-level column colour. Default, criteria: array (required). Array of {criterion, descriptors[]} objects. descriptors[] maps to levels[] by index.
spaced_repetition_card  — flip flashcard with confidence rating 1-5 — writes SRS interval to progress_store
  fields: front: string (required). Front face — term or question., back: string (required). Back face — answer or definition., card_id: string (optional). Key for progress_store SRS data. Auto-generated if omitted., accent: string (optional). Front card highlight colour. Default
leaderboard_card  — ranked score leaderboard — live on GAS from Sheet, static on web; medal top 3
  fields: course_id: string (required). Matches progress_store course_id., score_key: string (optional). Which quiz score to rank on. Default "quiz1"., limit: integer (optional). Max entries shown. Default 10., title: string (optional). Card heading. Default "Leaderboard"., items: array (optional, web/static). Array of {name, score} objects for static rendering.
  connectors: gas-native(apps-script-web,live); static(all-surfaces,static)
nav_bar  — named-page nav bar — generates ?nav= URLs at runtime from _A2UI_NAV; active page auto-highlighted
  fields: label: string (optional). Small uppercase label above the bar., layout: string (optional). "horizontal" (default) or "vertical"., sticky: boolean (optional). Whether to stick below the system nav header. Default true., top_offset: integer (optional). Top offset in px when sticky. Default 52., accent: string (optional). Active link accent colour. Default, links: array (required). Array of {nav_slug, label, icon?, active?} objects. nav_slug is the saved page slug; the correct URL is generated at runtime.
nav_link  — single CTA link to a named page — appends from= automatically for back-button support
  fields: nav_slug: string (required). Slug of the destination named page., label: string (optional). Button label. Default "Continue →"., icon: string (optional). Emoji or icon prefix., style: string (optional). "primary" (default), "ghost", or "text"., align: string (optional). "left" (default), "center", or "right".
breadcrumb  — breadcrumb trail linking named pages — current slug auto-highlighted from _A2UI_NAV
  fields: items: array (required). Array of {slug, label, icon?} objects in order from root to current page.`;
