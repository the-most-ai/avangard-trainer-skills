#!/usr/bin/env python3
"""Структурная самопроверка репозитория навыков. Бэкенд не требуется."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"

def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m: return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm

def main():
    errors, skills = [], 0
    seen = {}  # id -> skill в котором он объявлен (для кросс-скилл дублей)
    all_ids = set()
    if not SKILLS.is_dir():
        print("FAIL: нет .agents/skills/"); return 1
    for pdir in sorted(SKILLS.iterdir()):
        if not pdir.is_dir(): continue
        skills += 1
        sk = pdir / "SKILL.md"
        oy = pdir / "agents" / "openai.yaml"
        rf = pdir / "references" / "scenarios.md"
        if not sk.exists(): errors.append(f"{pdir.name}: нет SKILL.md"); continue
        fm = parse_frontmatter(sk.read_text(encoding="utf-8"))
        if not fm or "name" not in fm or "description" not in fm:
            errors.append(f"{pdir.name}: SKILL.md без name/description")
        if fm and fm.get("name") != pdir.name:
            errors.append(f"{pdir.name}: name != имени папки ({fm.get('name')})")
        if not oy.exists(): errors.append(f"{pdir.name}: нет agents/openai.yaml")
        else:
            y = oy.read_text(encoding="utf-8")
            if "create_training_profile" not in y:
                errors.append(f"{pdir.name}: openai.yaml не объявляет MCP create_training_profile")
            if 'type: "mcp"' not in y and "type: mcp" not in y:
                errors.append(f"{pdir.name}: openai.yaml без type: mcp")
        if not rf.exists(): errors.append(f"{pdir.name}: нет references/scenarios.md")
        else:
            # id сценариев берём из references (источник истины), дедуп внутри навыка
            local = set(re.findall(r"`([a-z]+\.[a-z_]+)`", rf.read_text(encoding="utf-8")))
            for i in local:
                if i in seen and seen[i] != pdir.name:
                    errors.append(f"id {i} объявлен в двух навыках: {seen[i]} и {pdir.name}")
                seen[i] = pdir.name
                all_ids.add(i)
    print(f"навыков: {skills} | уникальных id сценариев: {len(all_ids)}")
    if errors:
        print("FAIL:"); [print("  -", e) for e in errors]; return 1
    print("OK — структура репозитория валидна"); return 0

sys.exit(main())
