package ai.a2uicatalog.android

import androidx.a2ui.compose.runtime.A2uiComponentScope
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1.AccessibilityAttributes
import androidx.a2ui.compose.ui.catalog.A2uiBasicCatalogV1.CheckRule
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TimePicker
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.rememberTimePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import java.time.Instant
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

/*
 * The Basic Catalog's five input components. androidx.a2ui owns the data binding: each
 * TypedContent receives the bound value plus onValueChange, and the engine writes changes back
 * into the surface's data model, so a Button's action context carries what the user entered.
 * These only draw the Material 3 control.
 */

object DefaultTextField : A2uiBasicCatalogV1.TextField {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        label: String, value: String?, variant: A2uiBasicCatalogV1.TextField.Variant,
        validationRegexp: String?, onValueChange: (String) -> Unit, enabled: Boolean,
        accessibility: AccessibilityAttributes?, checks: List<CheckRule>, modifier: Modifier,
    ) {
        val value = value ?: ""
        val invalid = validationRegexp != null && value.isNotEmpty() &&
            runCatching { !Regex(validationRegexp).matches(value) }.getOrDefault(false)
        val long = variant == A2uiBasicCatalogV1.TextField.Variant.LongText
        OutlinedTextField(
            value = value, onValueChange = onValueChange, enabled = enabled,
            label = { Text(label) }, isError = invalid,
            singleLine = !long, minLines = if (long) 3 else 1,
            visualTransformation = if (variant == A2uiBasicCatalogV1.TextField.Variant.Obscured)
                PasswordVisualTransformation() else VisualTransformation.None,
            keyboardOptions = KeyboardOptions(keyboardType = when (variant) {
                A2uiBasicCatalogV1.TextField.Variant.Number -> KeyboardType.Number
                A2uiBasicCatalogV1.TextField.Variant.Obscured -> KeyboardType.Password
                else -> KeyboardType.Text
            }),
            modifier = modifier.fillMaxWidth(),
        )
    }
}

object DefaultCheckBox : A2uiBasicCatalogV1.CheckBox {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        label: String, value: Boolean, onValueChange: (Boolean) -> Unit, enabled: Boolean,
        accessibility: AccessibilityAttributes?, checks: List<CheckRule>, modifier: Modifier,
    ) {
        Row(
            modifier.fillMaxWidth()
                .toggleable(value = value, enabled = enabled, role = Role.Checkbox, onValueChange = onValueChange)
                .padding(vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Checkbox(checked = value, onCheckedChange = null, enabled = enabled)
            Text(label, Modifier.padding(start = 8.dp))
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
object DefaultChoicePicker : A2uiBasicCatalogV1.ChoicePicker {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        label: String?, options: List<A2uiBasicCatalogV1.ChoicePicker.Option>, value: List<String>,
        variant: A2uiBasicCatalogV1.ChoicePicker.Variant, displayStyle: A2uiBasicCatalogV1.ChoicePicker.DisplayStyle,
        filterable: Boolean, onValueChange: (List<String>) -> Unit, enabled: Boolean,
        accessibility: AccessibilityAttributes?, checks: List<CheckRule>, modifier: Modifier,
    ) {
        val multi = variant == A2uiBasicCatalogV1.ChoicePicker.Variant.MultipleSelection
        fun pick(v: String) = onValueChange(
            if (multi) (if (v in value) value - v else value + v) else listOf(v))
        var filter by remember { mutableStateOf("") }
        val shown = if (filterable && filter.isNotBlank())
            options.filter { it.label.contains(filter, ignoreCase = true) } else options
        Column(modifier.fillMaxWidth()) {
            label?.let { Text(it, style = MaterialTheme.typography.labelLarge, modifier = Modifier.padding(bottom = 4.dp)) }
            if (filterable) OutlinedTextField(filter, { filter = it }, label = { Text("Filter") },
                singleLine = true, modifier = Modifier.fillMaxWidth().padding(bottom = 4.dp))
            if (displayStyle == A2uiBasicCatalogV1.ChoicePicker.DisplayStyle.Chips) {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    shown.forEach { o ->
                        FilterChip(selected = o.value in value, onClick = { pick(o.value) },
                            label = { Text(o.label) }, enabled = enabled)
                    }
                }
            } else {
                shown.forEach { o ->
                    val sel = o.value in value
                    Row(
                        Modifier.fillMaxWidth().selectable(sel, enabled = enabled,
                            role = if (multi) Role.Checkbox else Role.RadioButton) { pick(o.value) }
                            .padding(vertical = 2.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        if (multi) Checkbox(sel, null, enabled = enabled) else RadioButton(sel, null, enabled = enabled)
                        Text(o.label, Modifier.padding(start = 8.dp))
                    }
                }
            }
        }
    }
}

object DefaultSlider : A2uiBasicCatalogV1.Slider {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        label: String?, min: Float, max: Float, value: Float, onValueChange: (Float) -> Unit,
        enabled: Boolean, accessibility: AccessibilityAttributes?, checks: List<CheckRule>, modifier: Modifier,
    ) {
        val lo = minOf(min, max)
        // Compose's Slider needs a non-empty range; a payload with min == max gets a fixed, disabled slider.
        val flat = !(maxOf(min, max) > lo)
        val hi = if (flat) lo + 1f else maxOf(min, max)
        Column(modifier.fillMaxWidth()) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(label ?: "", style = MaterialTheme.typography.labelLarge)
                Text(if (value % 1f == 0f) value.toInt().toString() else "%.2f".format(value),
                    style = MaterialTheme.typography.labelLarge)
            }
            Slider(value = value.coerceIn(lo, hi), onValueChange = onValueChange,
                valueRange = lo..hi, enabled = enabled && !flat)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
object DefaultDateTimeInput : A2uiBasicCatalogV1.DateTimeInput {
    @Composable
    override fun A2uiComponentScope.TypedContent(
        value: Long?, onValueChange: ((Long?) -> Unit)?, enableDate: Boolean, enableTime: Boolean,
        min: Long?, max: Long?, label: String?, accessibility: AccessibilityAttributes?,
        checks: List<CheckRule>, modifier: Modifier,
    ) {
        // Neither flag set means a date picker, the most common intent.
        val wantDate = enableDate || !enableTime
        var step by remember { mutableStateOf(0) }            // 0 closed, 1 date, 2 time
        var pickedDay by remember { mutableStateOf<Long?>(null) }
        val utc = value?.let { LocalDateTime.ofInstant(Instant.ofEpochMilli(it), ZoneOffset.UTC) }
        val shown = when {
            utc == null -> "Choose"
            wantDate && enableTime -> utc.format(DateTimeFormatter.ofPattern("d MMM yyyy, HH:mm"))
            wantDate -> utc.format(DateTimeFormatter.ofPattern("d MMM yyyy"))
            else -> utc.format(DateTimeFormatter.ofPattern("HH:mm"))
        }
        Column(modifier.fillMaxWidth()) {
            label?.let { Text(it, style = MaterialTheme.typography.labelLarge, modifier = Modifier.padding(bottom = 4.dp)) }
            // no onValueChange = the value is not bound to the data model, so it is read-only
            OutlinedButton(onClick = { step = if (wantDate) 1 else 2 }, enabled = onValueChange != null) { Text(shown) }
        }
        if (step == 1) {
            val state = rememberDatePickerState(initialSelectedDateMillis = value)
            DatePickerDialog(
                onDismissRequest = { step = 0 },
                confirmButton = {
                    TextButton(onClick = {
                        val day = state.selectedDateMillis
                        if (enableTime && day != null) { pickedDay = day; step = 2 }
                        else { onValueChange?.invoke(day?.let { clamp(it, min, max) }); step = 0 }
                    }) { Text("OK") }
                },
                dismissButton = { TextButton(onClick = { step = 0 }) { Text("Cancel") } },
            ) { DatePicker(state) }
        }
        if (step == 2) {
            val state = rememberTimePickerState(initialHour = utc?.hour ?: 9, initialMinute = utc?.minute ?: 0, is24Hour = true)
            AlertDialog(
                onDismissRequest = { step = 0 },
                confirmButton = {
                    TextButton(onClick = {
                        val base = pickedDay ?: value?.let { LocalDate.ofInstant(Instant.ofEpochMilli(it), ZoneOffset.UTC)
                            .atStartOfDay().toInstant(ZoneOffset.UTC).toEpochMilli() }
                            // time-only input with no value yet: today, not 1970
                            ?: LocalDate.now(ZoneOffset.UTC).atStartOfDay().toInstant(ZoneOffset.UTC).toEpochMilli()
                        onValueChange?.invoke(clamp(base + (state.hour * 60L + state.minute) * 60_000L, min, max))
                        step = 0
                    }) { Text("OK") }
                },
                dismissButton = { TextButton(onClick = { step = 0 }) { Text("Cancel") } },
                text = { TimePicker(state) },
            )
        }
    }

    private fun clamp(v: Long, min: Long?, max: Long?): Long =
        v.coerceAtLeast(min ?: Long.MIN_VALUE).coerceAtMost(max ?: Long.MAX_VALUE)
}
