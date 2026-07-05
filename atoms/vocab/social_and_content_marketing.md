---
category: social_and_content_marketing
title: Social & Content Marketing
atom_count: 21
platform_support:
  web: 21/21
  meet-stage: 0/21
  googlechat: 0/21
  google-apps-script-web: 20/21
  email: 0/21
  pdf: 0/21
maturity: stable
source: atoms/schema.yaml
---

# Social & Content Marketing

> 21 atoms · `*` = degraded (limited support) · Bold surface = full support

| Atom type | Description | Surfaces | Key fields |
|-----------|-------------|----------|------------|
| `testimonial_card` | customer testimonial with photo name and quote an optional avatar. | **Web/Blog** · **GAS Web App** · **PDF** | `text` — string<br>`author_name` — string<br>`author_title` — string<br>`author_avatar_url` — string<br>`rating` — integer |
| `avatar_group` | stacked user avatar group with overflow count or community. | **Web/Blog** · **GAS Web App** · **PDF** | `avatars` — list<br>`total_count` — integer<br>`label` — string |
| `contributor_list` | list of contributors with avatar and role community, with their | **Web/Blog** · **GAS Web App** · **PDF** | `contributors` — list<br>`title` — string |
| `customer_logo_grid` | grid of customer or partner logos | **Web/Blog** · **GAS Web App** · **PDF** | `logos` — list<br>`title` — string |
| `social_proof_banner` | social proof strip with stats and logos achievement. | **Web/Blog** · **GAS Web App** · **PDF** | `metric_value` — string<br>`metric_label` — string<br>`icon_url` — string<br>`link_url` — string |
| `media_mention_card` | press or media mention with logo and quote | **Web/Blog** · **GAS Web App** · **PDF** | `publication_name` — string<br>`publication_logo_url` — string<br>`headline` — string<br>`article_url` — string<br>`date` — string |
| `expert_endorsement` | expert quote with credentials and photo name, and credentials. | **Web/Blog** · **GAS Web App** · **PDF** | `quote` — string<br>`expert_name` — string<br>`expert_title` — string<br>`expert_organization` — string<br>`expert_avatar_url` — string |
| `review_callout` | highlighted customer review excerpt by a star rating. | **Web/Blog** · **GAS Web App** · **PDF** | `review_text` — string<br>`author_name` — string<br>`rating` — number<br>`max_rating` — integer<br>`product_name` — string |
| `social_feed_embed` | embedded social media post or feed or Instagram post. | **Web/Blog** | `embed_code` — string<br>`platform` — string<br>`post_url` — string |
| `social_share_bar` | social media buttons for sharing article to external networks | **Web/Blog** · **GAS Web App** | `platforms` — array. Permitted networks: twitter | linkedin | facebook | reddit.<br>`url` — string. Optional URL override, defaults to current page. |
| `newsletter_cta` | email subscription form for recurring reader updates | **Web/Blog** · **GAS Web App** | `headline` — string. Header message prompting subscription.<br>`button_label` — string. Optional submit button text, defaults to Subscribe. |
| `author_bio_card` | profile block displaying content creator biographical details | **Web/Blog** · **GAS Web App** | `name` — string. Full name of the content creator.<br>`avatar_url` — string. URL to the profile image.<br>`bio` — string. Short narrative profiling the writer.<br>`links` — object. Optional key-value pairs of platform names and URLs. |
| `related_posts_grid` | grid of recommended alternative post reading cards | **Web/Blog** · **GAS Web App** | `posts` — array. Objects containing title, url, and optional topic. |
| `series_overview_card` | navigation index for multi-part article series parts | **Web/Blog** · **GAS Web App** | `series_name` — string. Name of the series.<br>`parts` — array. Objects with title, url, and optional current boolean. |
| `reaction_group` | emoji reaction counters collecting reader sentiment feedback | **Web/Blog** · **GAS Web App** | `enabled_emojis` — array. Tracked emojis: thumbs_up | heart | rocket | mind_blown. |
| `share_quote` | prominent blockquote optimised for social media sharing | **Web/Blog** · **GAS Web App** | `text` — string. The impactful quote statement.<br>`author` — string. Optional attribution source. |
| `follow_cta` | call to action driving social media community expansion | **Web/Blog** · **GAS Web App** | `message` — string. Promotional copy driving user interactions.<br>`platform_links` — object. Platform name keys mapped to target URLs. |
| `follow_button` | direct profile subscription button for social platforms | **Web/Blog** · **GAS Web App** | `target_handle` — string. Handle identifier of target profile.<br>`platform` — string: twitter | github | linkedin. The platform. |
| `article_hero` | display prominent introductory headline and banner media | **Web/Blog** · **GAS Web App** | `title` — string. Main showcase headline text.<br>`subtitle` — string. Optional accompanying summary text.<br>`image_url` — string. URL to header background media. |
| `article_series_nav` | navigate interconnected parts inside multi-part blog series | **Web/Blog** · **GAS Web App** | `series_id` — string. Unique identifier of the series cluster.<br>`current_part` — integer. Ordered index within series limits. |
| `post_metadata_bar` | article metadata bar with author date read time | **Web/Blog** · **GAS Web App** | `author` — string. Author display name.<br>`date` — string. Publish date (YYYY-MM-DD).<br>`readTime` — integer. Estimated read time in minutes. |
