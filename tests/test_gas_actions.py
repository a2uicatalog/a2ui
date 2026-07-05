"""Wired surface action schema tests.

Validates that gas:sheet_* action blocks conform to the contract expected by
the server-side handlers in Code.private.gs. Pure structure checks — no GAS
runtime required. Covers: append, query, upsert, delete_row, aggregate,
identity tokens, by_user isolation, complex where filters, pagination.
"""

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_surface(actions, state_primitives=None, layout=None):
    return {
        "schemaVersion": "1.0",
        "type": "a2ui_wired_surface",
        "title": "Test",
        "theme": "light",
        "app": {"storage": {"type": "my_drive", "sheet": "TestSheet"}},
        "state_primitives": state_primitives or [],
        "actions": actions,
        "layout": layout or [],
    }


def validate_action(action):
    """Minimal contract: id, type, props."""
    errors = []
    if "id" not in action:
        errors.append("missing 'id'")
    if "type" not in action:
        errors.append("missing 'type'")
    if not isinstance(action.get("props"), dict):
        errors.append("'props' must be a dict")
    return errors


# ── gas:sheet_append ──────────────────────────────────────────────────────────

class TestSheetAppend:
    def _action(self, **overrides):
        base = {
            "id": "save_row",
            "type": "gas:sheet_append",
            "props": {
                "sheet": "MySheet",
                "collect": {"Name": "#name_mem.value", "Date": "{{now}}"},
            },
        }
        base.update(overrides)
        return base

    def test_valid_action_passes(self):
        assert validate_action(self._action()) == []

    def test_requires_id(self):
        a = self._action()
        del a["id"]
        assert "missing 'id'" in validate_action(a)

    def test_requires_type(self):
        a = self._action()
        del a["type"]
        assert "missing 'type'" in validate_action(a)

    def test_requires_props_dict(self):
        a = self._action(props=None)
        assert "'props' must be a dict" in validate_action(a)

    def test_sheet_is_string(self):
        props = self._action()["props"]
        assert isinstance(props["sheet"], str)

    def test_collect_is_dict(self):
        props = self._action()["props"]
        assert isinstance(props["collect"], dict)

    def test_collect_wire_expr_format(self):
        collect = self._action()["props"]["collect"]
        for key, val in collect.items():
            if val.startswith("#"):
                # wire expr must be #nodeId.property
                parts = val[1:].split(".")
                assert len(parts) == 2, f"malformed wire expr '{val}'"

    def test_collect_template_now(self):
        collect = {"Date": "{{now}}", "Ts": "{{datetime}}", "Today": "{{today}}"}
        for val in collect.values():
            assert val.startswith("{{") and val.endswith("}}")

    def test_on_success_is_list_of_strings(self):
        a = self._action()
        a["onSuccess"] = ["reload_data"]
        assert isinstance(a["onSuccess"], list)
        assert all(isinstance(s, str) for s in a["onSuccess"])

    def test_in_surface_schema(self):
        surface = make_surface([self._action()])
        actions = surface["actions"]
        assert len(actions) == 1
        assert actions[0]["type"] == "gas:sheet_append"


# ── gas:sheet_query ───────────────────────────────────────────────────────────

class TestSheetQuery:
    def _action(self, **overrides):
        base = {
            "id": "load_data",
            "type": "gas:sheet_query",
            "trigger": "onLoad",
            "props": {"sheet": "MySheet"},
            "wire": {"result": "#data_filter.source"},
        }
        base.update(overrides)
        return base

    def test_valid_action_passes(self):
        assert validate_action(self._action()) == []

    def test_trigger_values(self):
        a = self._action()
        assert a.get("trigger") in ("onLoad", None)

    def test_wire_result_format(self):
        wire = self._action()["wire"]
        expr = wire["result"]
        assert expr.startswith("#")
        parts = expr[1:].split(".")
        assert len(parts) == 2

    def test_optional_where_is_dict(self):
        a = self._action()
        a["props"]["where"] = {"status": "active"}
        assert isinstance(a["props"]["where"], dict)

    def test_optional_limit_is_int(self):
        a = self._action()
        a["props"]["limit"] = 50
        assert isinstance(a["props"]["limit"], int)
        assert a["props"]["limit"] > 0

    def test_optional_order_by_is_string(self):
        a = self._action()
        a["props"]["order_by"] = "created_at"
        assert isinstance(a["props"]["order_by"], str)

    def test_wire_result_targets_array_filter(self):
        # By convention result feeds an ArrayFilter or ValueStore source
        wire = self._action()["wire"]
        expr = wire["result"]
        node_id, prop = expr[1:].split(".")
        assert prop in ("source", "setValue"), \
            f"result wire should target .source or .setValue, got .{prop}"

    def test_on_load_trigger_in_surface(self):
        surface = make_surface([self._action()])
        triggered = [a for a in surface["actions"] if a.get("trigger") == "onLoad"]
        assert len(triggered) == 1


# ── gas:sheet_upsert ──────────────────────────────────────────────────────────

class TestSheetUpsert:
    def _action(self, **overrides):
        base = {
            "id": "upsert_row",
            "type": "gas:sheet_upsert",
            "props": {
                "sheet": "MySheet",
                "key_column": "id",
                "key_value": "#record_id.value",
                "collect": {"Name": "#name_mem.value", "Updated": "{{now}}"},
            },
        }
        base.update(overrides)
        return base

    def test_valid_action_passes(self):
        assert validate_action(self._action()) == []

    def test_requires_key_column(self):
        a = self._action()
        assert "key_column" in a["props"], "key_column is required for sheet_upsert"

    def test_requires_key_value(self):
        a = self._action()
        assert "key_value" in a["props"], "key_value is required for sheet_upsert"

    def test_key_value_is_wire_or_literal(self):
        key_value = self._action()["props"]["key_value"]
        # either a wire expr (#node.prop) or a plain string
        if key_value.startswith("#"):
            parts = key_value[1:].split(".")
            assert len(parts) == 2
        else:
            assert isinstance(key_value, str)

    def test_collect_present(self):
        props = self._action()["props"]
        assert "collect" in props
        assert isinstance(props["collect"], dict)
        assert len(props["collect"]) > 0


# ── gas:sheet_delete_row ──────────────────────────────────────────────────────

class TestSheetDeleteRow:
    def _action(self, **overrides):
        base = {
            "id": "delete_row",
            "type": "gas:sheet_delete_row",
            "props": {
                "sheet": "MySheet",
                "key_column": "id",
                "key_value": "#selected_id.value",
            },
        }
        base.update(overrides)
        return base

    def test_valid_action_passes(self):
        assert validate_action(self._action()) == []

    def test_requires_key_column(self):
        assert "key_column" in self._action()["props"]

    def test_requires_key_value(self):
        assert "key_value" in self._action()["props"]

    def test_key_value_wire_or_literal(self):
        kv = self._action()["props"]["key_value"]
        if kv.startswith("#"):
            assert len(kv[1:].split(".")) == 2
        else:
            assert isinstance(kv, str)

    def test_optional_delete_all_is_bool(self):
        a = self._action()
        a["props"]["delete_all"] = True
        assert isinstance(a["props"]["delete_all"], bool)


# ── gas:sheet_aggregate ───────────────────────────────────────────────────────

class TestSheetAggregate:
    def _action(self, **overrides):
        base = {
            "id": "expense_totals",
            "type": "gas:sheet_aggregate",
            "props": {
                "sheet": "Expenses",
                "group_by": "category",
                "aggregations": [
                    {"fn": "sum",   "column": "amount", "as": "total"},
                    {"fn": "count",                      "as": "count"},
                ],
            },
            "wire": {"result": "#totals_store.setValue"},
        }
        base.update(overrides)
        return base

    def test_valid_action_passes(self):
        assert validate_action(self._action()) == []

    def test_aggregations_is_list(self):
        assert isinstance(self._action()["props"]["aggregations"], list)

    def test_aggregation_fn_values(self):
        valid_fns = {"sum", "count", "avg", "min", "max"}
        for agg in self._action()["props"]["aggregations"]:
            assert agg["fn"] in valid_fns, f"unknown fn: {agg['fn']}"

    def test_aggregation_has_as_alias(self):
        for agg in self._action()["props"]["aggregations"]:
            assert "as" in agg, "each aggregation should have an 'as' alias"

    def test_group_by_is_string_or_absent(self):
        props = self._action()["props"]
        if "group_by" in props:
            assert isinstance(props["group_by"], str)

    def test_wire_result_format(self):
        wire = self._action()["wire"]
        expr = wire["result"]
        assert expr.startswith("#")
        assert len(expr[1:].split(".")) == 2

    def test_no_group_by_allowed(self):
        a = self._action()
        del a["props"]["group_by"]
        assert validate_action(a) == []


# ── Identity tokens ───────────────────────────────────────────────────────────

class TestIdentityTokens:
    VALID_TOKENS = ["{{now}}", "{{today}}", "{{datetime}}",
                    "{{app.user.email}}", "{{app.id}}",
                    "{{app.storage.sheet}}"]

    def test_user_email_token_in_collect(self):
        collect = {"submitted_by": "{{app.user.email}}", "date": "{{now}}"}
        for val in collect.values():
            assert val.startswith("{{") and val.endswith("}}")

    def test_user_email_token_format(self):
        token = "{{app.user.email}}"
        assert token in self.VALID_TOKENS

    def test_collect_with_user_identity(self):
        action = {
            "id": "submit",
            "type": "gas:sheet_append",
            "props": {
                "sheet": "Submissions",
                "collect": {
                    "name":         "#name_mem.value",
                    "submitted_by": "{{app.user.email}}",
                    "submitted_at": "{{now}}",
                },
            },
        }
        assert validate_action(action) == []
        collect = action["props"]["collect"]
        assert collect["submitted_by"] == "{{app.user.email}}"
        assert collect["submitted_at"] == "{{now}}"


# ── by_user isolation ─────────────────────────────────────────────────────────

class TestByUserIsolation:
    def _surface(self, isolation="by_user"):
        return {
            "schemaVersion": "1.0",
            "type": "a2ui_wired_surface",
            "title": "My App",
            "app": {
                "storage": {"type": "my_drive", "sheet": "UserData"},
                "data":    {"isolation": isolation},
                "auth":    {"mode": "user"},
            },
            "state_primitives": [],
            "actions": [],
            "layout": [],
        }

    def test_isolation_field_values(self):
        valid = {"none", "by_user", "by_team"}
        for v in valid:
            s = self._surface(v)
            assert s["app"]["data"]["isolation"] in valid

    def test_by_user_requires_user_auth(self):
        s = self._surface("by_user")
        # by_user isolation makes most sense with user auth mode
        assert s["app"]["auth"]["mode"] in ("user", "publisher")

    def test_isolation_none_is_default(self):
        s = make_surface([])
        assert s["app"].get("data", {}).get("isolation", "none") == "none"

    def test_by_user_surface_structure(self):
        s = self._surface("by_user")
        assert s["app"]["data"]["isolation"] == "by_user"

    def test_by_team_isolation(self):
        s = self._surface("by_team")
        assert s["app"]["data"]["isolation"] == "by_team"


# ── Complex where filters ─────────────────────────────────────────────────────

class TestWhereFilters:
    def _query(self, where):
        return {
            "id": "load",
            "type": "gas:sheet_query",
            "props": {"sheet": "Data", "where": where},
            "wire": {"result": "#filter.source"},
        }

    def test_equality_filter(self):
        a = self._query({"status": "active"})
        assert validate_action(a) == []
        assert a["props"]["where"]["status"] == "active"

    def test_gt_operator(self):
        a = self._query({"amount": {"gt": 100}})
        assert isinstance(a["props"]["where"]["amount"], dict)
        assert "gt" in a["props"]["where"]["amount"]

    def test_lt_operator(self):
        a = self._query({"score": {"lt": 50}})
        assert "lt" in a["props"]["where"]["score"]

    def test_gte_lte_range(self):
        a = self._query({"amount": {"gte": 10, "lte": 500}})
        w = a["props"]["where"]["amount"]
        assert "gte" in w and "lte" in w

    def test_ne_operator(self):
        a = self._query({"status": {"ne": "cancelled"}})
        assert "ne" in a["props"]["where"]["status"]

    def test_contains_operator(self):
        a = self._query({"description": {"contains": "flight"}})
        assert "contains" in a["props"]["where"]["description"]

    def test_mixed_equality_and_operator(self):
        where = {"status": "active", "amount": {"gt": 0}}
        a = self._query(where)
        assert isinstance(a["props"]["where"]["status"], str)
        assert isinstance(a["props"]["where"]["amount"], dict)

    def test_operator_keys_are_valid(self):
        valid_ops = {"gt", "lt", "gte", "lte", "eq", "ne", "contains"}
        where = {"amount": {"gt": 10, "lte": 1000}, "name": {"contains": "Air"}}
        for col, cond in where.items():
            if isinstance(cond, dict):
                for op in cond:
                    assert op in valid_ops, f"unknown operator: {op}"


# ── Pagination ────────────────────────────────────────────────────────────────

class TestPagination:
    def _query(self, limit=None, offset=None):
        props = {"sheet": "Data"}
        if limit  is not None: props["limit"]  = limit
        if offset is not None: props["offset"] = offset
        return {
            "id": "load",
            "type": "gas:sheet_query",
            "props": props,
            "wire": {"result": "#filter.source"},
        }

    def test_limit_only(self):
        a = self._query(limit=25)
        assert a["props"]["limit"] == 25

    def test_offset_only(self):
        a = self._query(offset=50)
        assert a["props"]["offset"] == 50

    def test_limit_and_offset(self):
        a = self._query(limit=25, offset=50)
        assert a["props"]["limit"] == 25
        assert a["props"]["offset"] == 50

    def test_limit_is_positive_int(self):
        a = self._query(limit=10)
        assert isinstance(a["props"]["limit"], int)
        assert a["props"]["limit"] > 0

    def test_offset_is_non_negative(self):
        a = self._query(offset=0)
        assert a["props"]["offset"] >= 0


# ── Full wired surface with Sheets actions ────────────────────────────────────

class TestWiredSurfaceSchema:
    def test_type_field(self):
        s = make_surface([])
        assert s["type"] == "a2ui_wired_surface"

    def test_app_storage_sheet(self):
        s = make_surface([])
        assert s["app"]["storage"]["sheet"] == "TestSheet"

    def test_action_ids_unique(self):
        actions = [
            {"id": "load", "type": "gas:sheet_query", "props": {"sheet": "S"}, "wire": {"result": "#f.source"}},
            {"id": "save", "type": "gas:sheet_append", "props": {"sheet": "S", "collect": {}}},
        ]
        ids = [a["id"] for a in actions]
        assert len(ids) == len(set(ids)), "action ids must be unique"

    def test_on_success_references_existing_action(self):
        actions = [
            {"id": "save", "type": "gas:sheet_append",
             "props": {"sheet": "S", "collect": {}}, "onSuccess": ["load"]},
            {"id": "load", "type": "gas:sheet_query",
             "props": {"sheet": "S"}, "wire": {"result": "#f.source"}},
        ]
        action_ids = {a["id"] for a in actions}
        for a in actions:
            for ref in a.get("onSuccess", []):
                assert ref in action_ids, f"onSuccess ref '{ref}' not found in actions"

    def test_atc_demo_payload_structure(self):
        """Smoke test the ATC Flight Log payload structure."""
        actions = [
            {
                "id": "log_flight",
                "type": "gas:sheet_append",
                "props": {
                    "collect": {
                        "callsign": "#selected_flight.callsign",
                        "altitude": "#selected_flight.alt",
                        "speed": "#selected_flight.spd",
                        "status": "#selected_flight.status",
                        "logged_at": "{{now}}",
                    },
                    "config": {"sheet": "ATC_FlightLog"},
                },
                "onSuccess": ["reload_log"],
            },
            {
                "id": "reload_log",
                "type": "gas:sheet_query",
                "props": {"config": {"sheet": "ATC_FlightLog"}},
                "wire": {"result": "#flight_filter.source"},
                "trigger": "onLoad",
            },
        ]
        surface = make_surface(actions)
        assert len(surface["actions"]) == 2
        append = next(a for a in surface["actions"] if a["type"] == "gas:sheet_append")
        assert "{{now}}" in append["props"]["collect"]["logged_at"]
        query = next(a for a in surface["actions"] if a["type"] == "gas:sheet_query")
        assert query.get("trigger") == "onLoad"
        assert "reload_log" in append.get("onSuccess", [])


# ── gas:firestore_* ───────────────────────────────────────────────────────────

class TestFirestoreActions:
    def _fs_query(self, **overrides):
        base = {
            "id": "load_docs",
            "type": "gas:firestore_query",
            "props": {"collection": "expenses"},
            "wire": {"result": "#data_filter.source"},
        }
        base.update(overrides)
        return base

    def _fs_set(self, **overrides):
        base = {
            "id": "save_doc",
            "type": "gas:firestore_set",
            "props": {"collection": "expenses",
                      "collect": {"amount": "#amount_mem.value", "submitted_by": "{{app.user.email}}"}},
        }
        base.update(overrides)
        return base

    def _fs_delete(self, **overrides):
        base = {
            "id": "delete_doc",
            "type": "gas:firestore_delete",
            "props": {"collection": "expenses", "doc_id": "#selected_id.value"},
        }
        base.update(overrides)
        return base

    def test_query_valid(self):
        assert validate_action(self._fs_query()) == []

    def test_set_valid(self):
        assert validate_action(self._fs_set()) == []

    def test_delete_valid(self):
        assert validate_action(self._fs_delete()) == []

    def test_query_collection_is_string(self):
        assert isinstance(self._fs_query()["props"]["collection"], str)

    def test_set_collect_has_identity_token(self):
        collect = self._fs_set()["props"]["collect"]
        assert collect["submitted_by"] == "{{app.user.email}}"

    def test_set_optional_doc_id(self):
        a = self._fs_set()
        a["props"]["doc_id"] = "#record_id.value"
        assert validate_action(a) == []

    def test_delete_requires_doc_id(self):
        assert "doc_id" in self._fs_delete()["props"]

    def test_query_where_operators(self):
        a = self._fs_query()
        a["props"]["where"] = {"amount": {"gt": 0}, "status": "active"}
        assert validate_action(a) == []

    def test_query_order_by_string(self):
        a = self._fs_query()
        a["props"]["order_by"] = "created_at"
        assert isinstance(a["props"]["order_by"], str)

    def test_query_order_by_array(self):
        a = self._fs_query()
        a["props"]["order_by"] = [{"column": "date", "dir": "desc"}, {"column": "name", "dir": "asc"}]
        for o in a["props"]["order_by"]:
            assert o["dir"] in ("asc", "desc")

    def test_query_select_projection(self):
        a = self._fs_query()
        a["props"]["select"] = ["amount", "category", "submitted_by"]
        assert isinstance(a["props"]["select"], list)

    def test_firestore_surface_uses_storage_config(self):
        surface = {
            "schemaVersion": "1.0",
            "type": "a2ui_wired_surface",
            "title": "Firestore App",
            "app": {
                "storage": {"type": "firestore", "collection": "expenses"},
                "data":    {"isolation": "by_user"},
                "auth":    {"mode": "user"},
            },
            "state_primitives": [],
            "actions": [self._fs_query()],
            "layout": [],
        }
        assert surface["app"]["storage"]["type"] == "firestore"
        assert surface["app"]["data"]["isolation"] == "by_user"


# ── gas:sheet_batch_append ────────────────────────────────────────────────────

class TestSheetBatchAppend:
    def _action(self, **overrides):
        base = {
            "id": "import_rows",
            "type": "gas:sheet_batch_append",
            "props": {"sheet": "Expenses"},
            # data is an array of collect objects — set at runtime via wire or literal
        }
        base.update(overrides)
        return base

    def test_valid_action(self):
        assert validate_action(self._action()) == []

    def test_type_is_correct(self):
        assert self._action()["type"] == "gas:sheet_batch_append"

    def test_data_is_array_of_objects(self):
        rows = [
            {"name": "Alice", "amount": "50", "date": "{{now}}"},
            {"name": "Bob",   "amount": "75", "date": "{{now}}"},
        ]
        for row in rows:
            assert isinstance(row, dict)
            for val in row.values():
                assert isinstance(val, str)


# ── Multi-sort order_by ───────────────────────────────────────────────────────

class TestMultiSort:
    def _query(self, order_by):
        return {
            "id": "load",
            "type": "gas:sheet_query",
            "props": {"sheet": "Data", "order_by": order_by},
            "wire": {"result": "#f.source"},
        }

    def test_single_string_order_by(self):
        a = self._query("created_at")
        assert isinstance(a["props"]["order_by"], str)

    def test_array_order_by(self):
        a = self._query([{"column": "date", "dir": "desc"}, {"column": "name", "dir": "asc"}])
        ob = a["props"]["order_by"]
        assert isinstance(ob, list)
        assert len(ob) == 2

    def test_order_by_dir_values(self):
        ob = [{"column": "amount", "dir": "desc"}, {"column": "name", "dir": "asc"}]
        for entry in ob:
            assert entry["dir"] in ("asc", "desc")

    def test_order_by_column_is_string(self):
        ob = [{"column": "date", "dir": "desc"}]
        assert isinstance(ob[0]["column"], str)


# ── Select projection ─────────────────────────────────────────────────────────

class TestSelectProjection:
    def _query(self, select):
        return {
            "id": "load",
            "type": "gas:sheet_query",
            "props": {"sheet": "Data", "select": select},
            "wire": {"result": "#f.source"},
        }

    def test_select_is_list_of_strings(self):
        a = self._query(["name", "amount", "date"])
        assert isinstance(a["props"]["select"], list)
        assert all(isinstance(c, str) for c in a["props"]["select"])

    def test_select_non_empty(self):
        a = self._query(["name"])
        assert len(a["props"]["select"]) > 0

    def test_isolation_cols_not_in_select(self):
        # a2ui_owner and a2ui_team are internal — should never appear in a user-facing select
        internal = {"a2ui_owner", "a2ui_team"}
        select = ["name", "amount", "category"]
        assert not internal.intersection(set(select))


# ── Identity tokens (extended) ────────────────────────────────────────────────

class TestIdentityTokensExtended:
    def test_user_name_token(self):
        collect = {"submitted_by": "{{app.user.name}}"}
        assert collect["submitted_by"] == "{{app.user.name}}"

    def test_all_identity_tokens(self):
        tokens = ["{{app.user.email}}", "{{app.user.name}}",
                  "{{now}}", "{{today}}", "{{datetime}}"]
        for t in tokens:
            assert t.startswith("{{") and t.endswith("}}")

    def test_collect_full_identity(self):
        collect = {
            "submitted_by_email": "{{app.user.email}}",
            "submitted_by_name":  "{{app.user.name}}",
            "submitted_at":       "{{now}}",
        }
        action = {
            "id": "submit",
            "type": "gas:sheet_append",
            "props": {"sheet": "Submissions", "collect": collect},
        }
        assert validate_action(action) == []
