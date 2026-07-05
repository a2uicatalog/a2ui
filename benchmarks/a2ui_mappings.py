"""
A2UI atom calls for each of the 7 OpenUI benchmark scenarios.

Each mapping represents what an LLM would output to describe the same UI
using the A2UI catalogue — component name + required/relevant fields only.
This is the "compiled vocabulary" advantage: layout/styling is zero-token,
precompiled into the renderer.
"""

# fmt: off

SCENARIOS = {

    # ── 1. Simple table ──────────────────────────────────────────────────────
    "simple-table": [
        {
            "component": "table",
            "headers": ["Name", "Department", "Salary", "YoY change (%)"],
            "rows": [
                ["Ava Patel",     "Engineering", 132000, 6.5],
                ["Marcus Lee",    "Sales",        98000, 4.2],
                ["Sofia Ramirez", "Marketing",   105000, 3.1],
                ["Ethan Brooks",  "Finance",     118500, 5.0],
                ["Nina Chen",     "HR",           89000, 2.4],
            ],
        }
    ],

    # ── 2. Contact form ───────────────────────────────────────────────────────
    "contact-form": [
        {"component": "form",
         "title": "Contact Us",
         "submit_label": "Submit",
         "cancel_label": "Cancel",
         "fields": [
             {"label": "Name",    "name": "name",    "type": "text",
              "placeholder": "Your full name",         "rules": ["required", "minLength:2"]},
             {"label": "Email",   "name": "email",   "type": "email",
              "placeholder": "you@example.com",        "rules": ["required", "email"]},
             {"label": "Phone",   "name": "phone",   "type": "text",
              "placeholder": "e.g. +1 555 123 4567",  "rules": ["required", "minLength:7", "maxLength:20"]},
             {"label": "Subject", "name": "subject", "type": "select",
              "options": [
                  {"value": "general",  "label": "General inquiry"},
                  {"value": "support",  "label": "Support"},
                  {"value": "sales",    "label": "Sales"},
                  {"value": "billing",  "label": "Billing"},
                  {"value": "feedback", "label": "Feedback"},
              ], "rules": ["required"]},
             {"label": "Message", "name": "message", "type": "textarea",
              "placeholder": "How can we help?",       "rules": ["required", "minLength:10"]},
         ]},
    ],

    # ── 3. Dashboard ─────────────────────────────────────────────────────────
    "dashboard": [
        {"component": "metric_comparison_card",
         "label": "Monthly Active Users",
         "value": "128,400",
         "delta": "+6.2% vs last month"},
        {"component": "metric_comparison_card",
         "label": "New Users (30d)",
         "value": "24,950",
         "delta": "+3.1%"},
        {"component": "metric_comparison_card",
         "label": "MRR",
         "value": "$412,000",
         "delta": "+4.4% MoM"},
        {"component": "metric_comparison_card",
         "label": "ARR",
         "value": "$4.94M",
         "delta": "+18.7% YoY"},
        {"component": "chartjs_bar",
         "title": "Monthly Active Users",
         "labels": ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"],
         "series": [{"name": "MAU",
                     "data": [84500,87200,90100,93800,96500,100200,
                              104800,109600,114300,119900,123700,128400]}]},
        {"component": "chartjs_line",
         "title": "Revenue Trend",
         "labels": ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"],
         "series": [
             {"name": "MRR ($)",
              "data": [332000,341000,349000,356000,364000,372000,
                       381000,389000,397000,404000,408000,412000]},
             {"name": "ARR ($)",
              "data": [3984000,4092000,4188000,4272000,4368000,4464000,
                       4572000,4668000,4764000,4848000,4896000,4944000]},
         ]},
        {"component": "table",
         "headers": ["Feature", "Weekly Active Users", "Adoption Rate (%)", "Avg. Uses / User"],
         "rows": [
             ["Dashboards",         48200, 62.5, 5.8],
             ["Automations",        31750, 41.2, 3.1],
             ["Integrations",       28900, 37.5, 2.4],
             ["Team Collaboration", 27100, 35.2, 4.6],
             ["Exports",            19850, 25.8, 1.7],
             ["Alerts",             17600, 22.9, 2.0],
             ["API Access",         12150, 15.8, 6.3],
         ]},
    ],

    # ── 4. Pricing page ───────────────────────────────────────────────────────
    "pricing-page": [
        {"component": "pricing_tier_group",
         "tiers": [
             {"name": "Basic",      "price": "$12/mo",    "cta": "Start Basic"},
             {"name": "Pro",        "price": "$29/mo",    "cta": "Choose Pro",   "highlight": True},
             {"name": "Enterprise", "price": "Custom",    "cta": "Contact Sales"},
         ]},
        {"component": "feature_matrix",
         "features": ["Workspaces", "Projects", "Storage", "Automations",
                      "SSO/SAML", "Audit logs", "Support"],
         "tiers":    ["Basic", "Pro", "Enterprise"]},
        {"component": "faq_accordion",
         "items": [
             {"q": "Can I switch plans later?",      "a": "Yes — upgrade/downgrade anytime."},
             {"q": "Free trial?",                     "a": "Yes for Basic and Pro."},
             {"q": "Annual billing?",                 "a": "Yes, with a discount."},
             {"q": "Security and compliance?",        "a": "SSO, SCIM, audit logs on Enterprise."},
         ]},
    ],

    # ── 5. Chart with data ────────────────────────────────────────────────────
    "chart-with-data": [
        {"component": "metric_comparison_card",
         "label": "Total Revenue",
         "value": "$1,284,000",
         "delta": "+8.4% vs prior 6 months"},
        {"component": "chartjs_bar",
         "title": "Monthly Revenue",
         "labels": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
         "series": [{"name": "Revenue",
                     "data": [198000, 205000, 214000, 210000, 223000, 234000]}]},
    ],

    # ── 6. E-commerce product ─────────────────────────────────────────────────
    "e-commerce-product": [
        {"component": "image_pair",
         "images": [
             "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
             "https://images.unsplash.com/photo-1528701800489-20be3c1ea3b1",
         ]},
        {"component": "stat_card",
         "label": "AeroStride Runner",
         "value": "$129.00",
         "delta": "In stock",
         "sublabel": "Lightweight daily trainer"},
        {"component": "badge_group",
         "badges": ["Breathable mesh", "Responsive foam", "Rubber outsole",
                    "Everyday training"]},
        {"component": "table",
         "headers": ["Detail", "Value"],
         "rows": [
             ["Weight",   "9.8 oz (US 9)"],
             ["Drop",     "8 mm"],
             ["Upper",    "Engineered mesh"],
             ["Midsole",  "EVA-based foam"],
             ["Outsole",  "High-abrasion rubber"],
             ["Care",     "Spot clean; air dry"],
         ]},
        {"component": "callout",
         "type": "info",
         "title": "Fit note",
         "body": "True to size. If between sizes, consider going up 0.5."},
    ],

    # ── 7. Settings panel ─────────────────────────────────────────────────────
    "settings-panel": [
        {"component": "tabs",
         "items": ["Profile", "Security", "Notifications"]},
        # Profile tab — form with display name + avatar URL
        {"component": "form",
         "title": "Profile",
         "submit_label": "Save changes",
         "cancel_label": "Reset",
         "fields": [
             {"label": "Display name", "name": "display_name", "type": "text",
              "placeholder": "e.g. Alex Johnson",
              "rules": ["required", "minLength:2", "maxLength:60"]},
             {"label": "Avatar URL", "name": "avatar_url", "type": "url",
              "placeholder": "https://example.com/avatar.png",
              "rules": ["url"]},
         ]},
        # Security tab — switch group
        {"component": "form_switch_group",
         "label": "Security",
         "name": "security",
         "items": [
             {"name": "two_fa", "label": "Two-factor authentication (2FA)",
              "description": "Require a verification code when signing in.",
              "default_checked": False},
         ]},
        {"component": "callout",
         "type": "info",
         "title": "Tip",
         "body": "After enabling 2FA you may be asked to set up an authenticator app or backup codes."},
        # Notifications tab — switch group
        {"component": "form_switch_group",
         "label": "Notifications",
         "name": "notifications",
         "items": [
             {"name": "notif_email",    "label": "Email notifications",
              "description": "Receive updates and account messages by email.",
              "default_checked": True},
             {"name": "notif_product",  "label": "Product updates",
              "description": "Get notified about new features and improvements.",
              "default_checked": False},
             {"name": "notif_security", "label": "Security alerts",
              "description": "Important alerts about sign-ins and security changes.",
              "default_checked": True},
         ]},
    ],
}
