from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import zipfile
import xml.etree.ElementTree as ET

# Platforms mapping between sheet labels and model platforms
PLATFORM_MAP = {
    'IG': 'Instagram',
    'Instagram': 'Instagram',
    'TT': 'TikTok',
    'TikTok': 'TikTok',
    'YT': 'YouTube',
    'YouTube': 'YouTube',
    'FB': 'Facebook',
    'Facebook': 'Facebook',
}


def _col_letter_to_index(col: str) -> int:
    """Convert Excel column letter (A, B, ..., Z, AA, AB, ...) to 0-based index."""
    result = 0
    for char in col.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def _xlsx_read_rows(xlsx_path: Path) -> Dict[str, List[List[str]]]:
    ns_main = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    ns_r = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

    with zipfile.ZipFile(xlsx_path) as z:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = wb.find(f'{{{ns_main}}}sheets')
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rid_to_target = {rel.attrib.get('Id'): rel.attrib.get('Target') for rel in rels}

        # Load shared strings
        shared_strings: List[str] = []
        if 'xl/sharedStrings.xml' in z.namelist():
            sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in sst:
                texts = []
                for t in si.iter(f'{{{ns_main}}}t'):
                    texts.append(t.text or '')
                shared_strings.append(''.join(texts))

        def get_text(c) -> str:
            v = c.find(f'{{{ns_main}}}v')
            t = c.attrib.get('t')
            if v is None:
                is_ = c.find(f'{{{ns_main}}}is')
                if is_ is not None:
                    texts = [t.text or '' for t in is_.iter(f'{{{ns_main}}}t')]
                    return ''.join(texts)
                return ''
            val = v.text or ''
            if t == 's':
                try:
                    idx = int(val)
                    return shared_strings[idx] if 0 <= idx < len(shared_strings) else val
                except Exception:
                    return val
            return val

        def get_col_from_ref(ref: str) -> str:
            """Extract column letters from cell reference like 'A1', 'AB23'."""
            col = ''
            for ch in ref:
                if ch.isalpha():
                    col += ch
                else:
                    break
            return col

        out: Dict[str, List[List[str]]] = {}
        for sh in sheets:
            name = sh.attrib.get('name')
            rid = sh.attrib.get(f'{{{ns_r}}}id')
            target = rid_to_target.get(rid)
            path = 'xl/' + target if target and not target.startswith('xl/') else (target or '')
            if not path:
                continue
            xml = ET.fromstring(z.read(path))
            sheetData = xml.find(f'{{{ns_main}}}sheetData')
            rows: List[List[str]] = []
            if sheetData is not None:
                for row in sheetData:
                    # Build row with proper column alignment using cell references
                    cells = list(row)
                    if not cells:
                        rows.append([])
                        continue
                    # Find max column index
                    max_col_idx = 0
                    for c in cells:
                        ref = c.attrib.get('r', '')
                        col = get_col_from_ref(ref)
                        if col:
                            max_col_idx = max(max_col_idx, _col_letter_to_index(col))
                    # Create row with proper size and fill in values at correct positions
                    row_data = [''] * (max_col_idx + 1)
                    for c in cells:
                        ref = c.attrib.get('r', '')
                        col = get_col_from_ref(ref)
                        if col:
                            col_idx = _col_letter_to_index(col)
                            row_data[col_idx] = get_text(c)
                    rows.append(row_data)
            out[name] = rows
        return out


def _to_float(x: str) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).replace(',', '').strip()
        if s == '':
            return None
        return float(s)
    except Exception:
        return None


def _extract_historical_mom(rows: List[List[str]]) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for r in rows:
        if not r:
            continue
        label = str(r[0]).strip()
        if label in PLATFORM_MAP:
            # pick a plausible monthly MoM growth value in (0, 0.2)
            candidates = [v for v in (_to_float(c) for c in r[1:]) if v is not None and 0 < v < 0.2]
            if candidates:
                result[PLATFORM_MAP[label]] = max(candidates)  # prefer the larger MoM among row cells
    return result


def _extract_projected_mom(rows: List[List[str]]) -> Dict[str, float]:
    # find header with 'Projected Growth'
    proj_idx = None
    for r in rows[:5]:
        if any('Projected Growth' in str(c) for c in r):
            proj_idx = next((i for i, c in enumerate(r) if 'Projected Growth' in str(c)), None)
            break
    result: Dict[str, float] = {}
    for r in rows:
        if not r:
            continue
        label = str(r[0]).strip()
        if label in ('TikTok', 'Instagram', 'Facebook', 'YouTube'):
            if proj_idx is not None and proj_idx < len(r):
                v = _to_float(r[proj_idx])
                if v is not None and 0 < v < 0.3:
                    result[label] = v
            else:
                # fallback: second numeric in row
                nums = [v for v in (_to_float(c) for c in r[1:]) if v is not None and 0 < v < 0.3]
                if nums:
                    result[label] = max(nums)
    return result


def _extract_followers_per_view(rows: List[List[str]]) -> Optional[float]:
    # Prefer a single value row ~0.0001 to 0.05
    for r in rows:
        if len(r) == 1:
            v = _to_float(r[0])
            if v is not None and 0 < v < 0.05:
                return v
    # Fallback: TOTAL row with views and followers
    for r in rows:
        if r and str(r[0]).strip().upper() == 'TOTAL':
            nums = [v for v in (_to_float(c) for c in r[1:]) if v is not None and v > 0]
            if len(nums) >= 2:
                # choose largest as views, smallest as followers
                views = max(nums)
                followers = min(nums)
                if views > 0:
                    return followers / views
    return None


def _extract_carebears_views_per_post(rows: List[List[str]]) -> Dict[str, float]:
    """Return approximate views per post per platform using the Care Bears block in Competitor Benchmarks."""
    out: Dict[str, float] = {}
    active = False
    for r in rows:
        if not r:
            continue
        if not active and any('Care Bears' in str(c) for c in r):
            active = True
            continue
        if active:
            label = str(r[0]).strip()
            # Stop if another brand header appears
            if label in ('Barbie', 'Strawberry Shortcake', 'Peanuts', 'Hello Kitty', 'Squishmallows', 'CreativeInc'):
                break
            posts = _to_float(r[1]) if len(r) > 1 else None
            views = _to_float(r[2]) if len(r) > 2 else None
            if posts and views and posts > 0:
                if label.startswith('IG Reels'):
                    out['Instagram'] = views / posts
                elif label.startswith('FB Reels'):
                    out['Facebook'] = views / posts
                elif label.startswith('TT') or label.startswith('TikTok'):
                    out['TikTok'] = views / posts
                elif label.startswith('YT') or label.startswith('YouTube'):
                    out['YouTube'] = views / posts
    return out


def _extract_cpf_overrides(rows: List[List[str]]) -> Dict[str, Dict[str, float]]:
    """Extract CPF midpoints from TOTAL rows across the two tables.
    Returns dict with keys: cpf_paid_mid, cpf_creator_mid.
    """
    cpf_paid_vals: List[float] = []
    cpf_creator_vals: List[float] = []

    table = 0
    for r in rows:
        if not r:
            continue
        if r[0] == 'Channel' and 'Est CPV' in r:
            table = 2
            continue
        if r[0] == 'Channel' and 'Est CPT' in r:
            table = 1
            continue
        if str(r[0]).strip() == 'TOTAL':
            # Cost Per Follow likely present near end of row
            nums = [v for v in (_to_float(c) for c in r) if v is not None]
            if nums:
                last = nums[-1]
                if table == 2:
                    cpf_paid_vals.append(last)
                elif table == 1:
                    cpf_paid_vals.append(last)
        if str(r[0]).strip() == 'Creators':
            nums = [v for v in (_to_float(c) for c in r) if v is not None]
            if nums:
                last = nums[-1]
                cpf_creator_vals.append(last)

    def _mid(vals: List[float], default: float) -> float:
        return sum(vals) / len(vals) if vals else default

    return {
        'cpf_paid': {'min': 3.0, 'mid': _mid(cpf_paid_vals, 5.0), 'max': 6.0},
        'cpf_creator': {'min': 10.0, 'mid': _mid(cpf_creator_vals, 12.5), 'max': 20.0}
    }


def load_calibration_from_xlsx(xlsx_path: Path) -> Dict[str, Any]:
    rows_by_sheet = _xlsx_read_rows(xlsx_path)

    # Historical MoM floors
    hist = _extract_historical_mom(rows_by_sheet.get('Historical Growth', []))
    # Projected MoM bounds
    proj = _extract_projected_mom(rows_by_sheet.get('Projected Follower Growth', []))
    # Followers per view
    fpv = _extract_followers_per_view(rows_by_sheet.get('Views and Engagements past 8 mo', []))
    # Views per post per platform from Care Bears block
    vpp = _extract_carebears_views_per_post(rows_by_sheet.get('Competitor Benchmarks', []))
    # CPF overrides from paid/creator tables
    cpf = _extract_cpf_overrides(rows_by_sheet.get('Paid and Creators CPT', []))

    # Build overrides
    base_monthly_rate = hist if hist else None

    # Platform caps: use projected MoM + headroom; clamp to at least current defaults if missing
    platform_monthly_cap = None
    if proj:
        platform_monthly_cap = {k: min(max(v * 1.6, 0.04), 0.15) for k, v in proj.items()}

    per_post_gain_base = None
    if fpv and vpp:
        per_post_gain_base = {k: max(fpv * v, 1.0) for k, v in vpp.items()}

    out = {
        'base_monthly_rate': base_monthly_rate,
        'platform_monthly_cap': platform_monthly_cap,
        'per_post_gain_base': per_post_gain_base,
        'cpf_paid': cpf.get('cpf_paid'),
        'cpf_creator': cpf.get('cpf_creator'),
        # seasonality: gentle 2% monthly decay to align with slowing growth chart
        'month_decay_per_month': 0.02,
    }
    return out


def _excel_serial_to_date(serial: float) -> datetime:
    """Convert Excel serial number to datetime."""
    from datetime import timedelta
    if serial > 59:
        serial -= 1  # Excel bug: 1900 was not a leap year
    return datetime(1899, 12, 30) + timedelta(days=serial)


def load_follower_history_from_xlsx(xlsx_path: Path) -> Dict[str, Any]:
    """Parse follower history from the workbook.
    Prefers the 'Care Bears Data' tab with explicit per-month, per-platform values.
    Falls back to 'Growth Chart' tab, then reconstructing from 'Historical Growth' if needed.
    """
    rows_by_sheet = _xlsx_read_rows(xlsx_path)

    # 0) Try 'Care Bears Data' sheet first (new preferred source)
    cbd = rows_by_sheet.get('Care Bears Data', [])
    if cbd and len(cbd) >= 6:
        # Find the rows by looking for platform names in column A
        # The sheet has multiple sections (Followers, # of posts, Engagement %, Views)
        # We only want the Followers section which starts with row labeled "Followers"
        date_row = None
        platform_rows: Dict[str, List[str]] = {}
        in_followers_section = False

        for r in cbd:
            if not r:
                # Empty row might signal end of section
                if in_followers_section and platform_rows:
                    break  # Stop after we've captured the Followers section
                continue
            label = str(r[0]).strip() if r else ''
            if label == 'Followers':
                date_row = r
                in_followers_section = True
            elif in_followers_section:
                # Only capture platforms when we're in the Followers section
                if label == 'YouTube':
                    platform_rows['YouTube'] = r
                elif label == 'TikTok':
                    platform_rows['TikTok'] = r
                elif label == 'Instagram':
                    platform_rows['Instagram'] = r
                elif label == 'Facebook':
                    platform_rows['Facebook'] = r
                elif label and label != '' and label not in ('YouTube', 'TikTok', 'Instagram', 'Facebook'):
                    # Hit a different section header, stop
                    break

        if date_row and platform_rows:
            # Parse dates from row (Excel serial numbers)
            # Shift dates forward by 2 months so data shows Jan 2025 - Nov 2025 + Dec 2025 (interpolated)
            from dateutil.relativedelta import relativedelta
            labels: List[str] = []
            for i, cell in enumerate(date_row[1:], 1):
                val = _to_float(cell)
                if val and val > 40000:  # Excel date serial
                    try:
                        dt = _excel_serial_to_date(val)
                        # Shift forward by 2 months
                        dt = dt + relativedelta(months=2)
                        labels.append(dt.strftime('%b %Y'))
                    except:
                        labels.append(f'Col{i}')
                elif cell and str(cell).strip():
                    labels.append(str(cell).strip())

            # Build data rows for each month
            max_cols = len(labels)
            data_rows: List[Dict[str, Any]] = []

            for i in range(max_cols):
                row: Dict[str, Any] = {"label": labels[i] if i < len(labels) else f"H{i+1}"}
                total = 0.0
                has_data = False

                for pname in ("Instagram", "TikTok", "YouTube", "Facebook"):
                    if pname in platform_rows:
                        pr = platform_rows[pname]
                        # Column index is i+1 (skip column A)
                        if i + 1 < len(pr):
                            val = _to_float(pr[i + 1])
                            if val is not None and val > 0:
                                row[pname] = float(val)
                                total += float(val)
                                has_data = True

                if has_data:
                    row['Total'] = float(total)
                    data_rows.append(row)

            if data_rows:
                # Interpolate missing platform data to avoid jumps
                platforms = ["Instagram", "TikTok", "YouTube", "Facebook"]

                for pname in platforms:
                    # Collect indices where we have data
                    vals = [(i, data_rows[i].get(pname)) for i in range(len(data_rows))]
                    known = [(i, v) for i, v in vals if v is not None]

                    if len(known) < 2:
                        # Not enough data to interpolate - use first/last known value
                        if known:
                            single_val = known[0][1]
                            single_idx = known[0][0]
                            # Mark all as interpolated except the known one
                            for i in range(len(data_rows)):
                                if i != single_idx:
                                    data_rows[i][pname] = single_val
                                    data_rows[i][f'{pname}_interpolated'] = True
                        continue

                    # Linear interpolation for gaps
                    for i in range(len(data_rows)):
                        if data_rows[i].get(pname) is None:
                            # Find nearest known values before and after
                            before = [(idx, v) for idx, v in known if idx < i]
                            after = [(idx, v) for idx, v in known if idx > i]

                            if before and after:
                                # Interpolate between
                                bi, bv = before[-1]
                                ai, av = after[0]
                                ratio = (i - bi) / (ai - bi)
                                interpolated = bv + (av - bv) * ratio
                                data_rows[i][pname] = float(interpolated)
                                data_rows[i][f'{pname}_interpolated'] = True
                            elif before:
                                # Extrapolate forward using last known growth rate
                                if len(before) >= 2:
                                    (i1, v1), (i2, v2) = before[-2], before[-1]
                                    monthly_growth = (v2 - v1) / (i2 - i1) if i2 != i1 else 0
                                    extrapolated = v2 + monthly_growth * (i - i2)
                                else:
                                    extrapolated = before[-1][1]
                                data_rows[i][pname] = float(max(extrapolated, 0))
                                data_rows[i][f'{pname}_interpolated'] = True
                            elif after:
                                # Extrapolate backward
                                if len(after) >= 2:
                                    (i1, v1), (i2, v2) = after[0], after[1]
                                    monthly_growth = (v2 - v1) / (i2 - i1) if i2 != i1 else 0
                                    extrapolated = v1 - monthly_growth * (i1 - i)
                                else:
                                    extrapolated = after[0][1]
                                data_rows[i][pname] = float(max(extrapolated, 0))
                                data_rows[i][f'{pname}_interpolated'] = True

                # Recalculate totals and mark if any component was interpolated
                for row in data_rows:
                    total = 0.0
                    any_interpolated = False
                    for pname in platforms:
                        if pname in row and row[pname] is not None:
                            total += row[pname]
                            if row.get(f'{pname}_interpolated'):
                                any_interpolated = True
                    row['Total'] = float(total)
                    if any_interpolated:
                        row['Total_interpolated'] = True

                # Mark Dec 2025 as interpolated (projected/estimated data)
                # After date shift, the last row is Dec 2025 which is based on Oct 2025 Excel data
                # We mark it as interpolated since it's effectively a projection
                if data_rows and data_rows[-1].get('label') == 'Dec 2025':
                    last_row = data_rows[-1]
                    for pname in platforms:
                        if pname in last_row:
                            last_row[f'{pname}_interpolated'] = True
                    last_row['Total_interpolated'] = True

                return {"labels": [r['label'] for r in data_rows], "data": data_rows}

    # Helper: build payload from labeled columns
    def build_from_table(header: List[str], table: Dict[str, List[Optional[float]]], hint_end: Optional[Tuple[str, int]] = None) -> Dict[str, Any]:
        labels_raw = [h for h in header if isinstance(h, str) and h.strip()]
        # Normalize lengths
        max_len = 0
        for v in table.values():
            max_len = max(max_len, len(v))
        labels_raw = labels_raw[:max_len]

        # Infer years for header labels
        month_names = ['January','February','March','April','May','June','July','August','September','October','November','December']
        m2i = {m.lower(): i for i, m in enumerate(month_names)}
        def m_index(name: str) -> int:
            return m2i.get((name or '').strip().lower(), 0)

        years: List[Optional[int]] = [None] * len(labels_raw)
        if labels_raw:
            if hint_end:
                end_month, end_year = hint_end
                # anchor last occurrence of end_month
                end_idx = None
                for i in reversed(range(len(labels_raw))):
                    if (labels_raw[i] or '').strip().lower().startswith(end_month.lower()):
                        end_idx = i
                        break
                if end_idx is not None:
                    years[end_idx] = end_year
                    # backfill
                    for k in range(end_idx-1, -1, -1):
                        years[k] = (years[k+1] - 1) if m_index(labels_raw[k]) > m_index(labels_raw[k+1]) else years[k+1]
                    # forward fill
                    for k in range(end_idx+1, len(labels_raw)):
                        years[k] = (years[k-1] + 1) if m_index(labels_raw[k]) < m_index(labels_raw[k-1]) else years[k-1]
            # If still missing, start from current year and roll on Jan
            if any(y is None for y in years):
                base = datetime.now().year
                years = [None] * len(labels_raw)
                years[0] = base
                for k in range(1, len(labels_raw)):
                    years[k] = (years[k-1] + 1) if m_index(labels_raw[k]) < m_index(labels_raw[k-1]) else years[k-1]

        # Build display labels like 'Apr 2025'
        def abbr(name: str) -> str:
            return (name or '')[:3].title()
        labels = [f"{abbr(labels_raw[i])} {years[i]}" if i < len(labels_raw) and years[i] is not None else (labels_raw[i] if i < len(labels_raw) else f"H{i+1}") for i in range(max_len)]

        data_rows: List[Dict[str, Any]] = []
        for i in range(max_len):
            row: Dict[str, Any] = {"label": labels[i] if i < len(labels) else f"H{i+1}"}
            total = 0.0
            for pname in ("Instagram","TikTok","YouTube","Facebook"):
                arr = table.get(pname, [])
                val = arr[i] if i < len(arr) else None
                if val is not None:
                    row[pname] = float(val)
                    total += float(val)
            # Use table-provided Total if present, else compute
            tarr = table.get('Total')
            row['Total'] = float(tarr[i]) if tarr and i < len(tarr) and tarr[i] is not None else float(total)
            data_rows.append(row)
        return {"labels": labels, "data": data_rows}

    # 1) Try Growth Chart
    gc = rows_by_sheet.get('Growth Chart', [])
    if gc:
        # Header row is row 0
        header = [str(c).strip() for c in gc[0][1:]] if len(gc) > 0 else []
        # Map sheet short names
        name_map = {
            'INSTA': 'Instagram',
            'IG': 'Instagram',
            'TT': 'TikTok',
            'TikTok': 'TikTok',
            'FB': 'Facebook',
            'Facebook': 'Facebook',
            'YT': 'YouTube',
            'YouTube': 'YouTube',
            'Followers (TOTAL)': 'Total',
        }
        table: Dict[str, List[Optional[float]]] = {k: [] for k in ['Total','Instagram','TikTok','YouTube','Facebook']}
        # Parse hint from 'Views and Engagements past 8 mo'
        hint_end: Optional[Tuple[str, int]] = None
        rng_rows = rows_by_sheet.get('Views and Engagements past 8 mo', [])
        for r in rng_rows[:5]:
            s = ' '.join(str(c) for c in r if c)
            if 'months' in s and '-' in s:
                # naive capture of trailing '<Mon> <Year>'
                toks = s.replace('\u00A0',' ').split()
                if len(toks) >= 2:
                    mon = toks[-2]
                    try:
                        yr = int(toks[-1])
                        hint_end = (mon, yr)
                        break
                    except Exception:
                        pass
        # Parse rows into table
        for r in gc[1:]:
            if not r:
                continue
            key = name_map.get(str(r[0]).strip())
            if not key:
                continue
            # Convert cells to floats (skip header cell)
            vals: List[Optional[float]] = []
            for c in r[1:]:
                vals.append(_to_float(c))
            # Normalize trailing empties
            while vals and vals[-1] is None:
                vals.pop()
            table[key] = vals
        # If we have at least one platform series, build payload
        if any(len(v) > 0 for k, v in table.items() if k != 'Total'):
            return build_from_table(header, table, hint_end)

    # 2) Fallback: reconstruct from Historical Growth (start/end)
    rows = rows_by_sheet.get('Historical Growth', [])
    def find_row(prefix: str) -> Optional[List[float]]:
        for r in rows:
            if not r:
                continue
            if str(r[0]).strip() == prefix:
                nums = [_to_float(c) for c in r[1:6]]
                nums = [n for n in nums if n is not None]
                if len(nums) >= 2 and nums[0] > 0 and nums[1] > 0:
                    return nums[:2]
        return None

    series: Dict[str, List[float]] = {}
    platforms = [('Instagram', 'IG'), ('TikTok', 'TT'), ('Facebook', 'FB'), ('YouTube', 'YT')]
    count_months = 8
    for pname, short in platforms:
        vals = find_row(short)
        if not vals:
            continue
        start, end = vals
        try:
            r = (end / start) ** (1.0 / count_months) - 1.0 if start > 0 else 0.0
        except Exception:
            r = 0.0
        seq = [start * ((1 + r) ** i) for i in range(0, count_months + 1)]
        series[pname] = [float(x) for x in seq]

    if not series:
        return {"labels": [], "data": []}

    labels = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][: len(next(iter(series.values())))]
    data_rows: List[Dict[str, Any]] = []
    for i, _ in enumerate(labels):
        row: Dict[str, Any] = {"label": labels[i]}
        total = 0.0
        for pname, _ in platforms:
            if pname in series and i < len(series[pname]):
                row[pname] = float(series[pname][i])
                total += float(series[pname][i])
        row['Total'] = float(total)
        data_rows.append(row)
    return {"labels": labels, "data": data_rows}
