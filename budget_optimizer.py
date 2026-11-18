"""Budget-aware BOM trade-offs for Lumen quote estimates."""


PORT_DOWNGRADES = {
    "400G_Port": "100G_Port",
    "100G_Port": "10G_Port",
    "10G_Port": "1G_Port",
}
OPTIC_DOWNGRADES = {
    "Optic_400G": "Optic_100G",
    "Optic_100G": "Optic_10G",
    "Optic_10G": "Optic_1G",
}
PORT_OPTICS = {
    "400G_Port": "Optic_400G",
    "100G_Port": "Optic_100G",
    "10G_Port": "Optic_10G",
    "1G_Port": "Optic_1G",
}


def calculate_mrc(bom):
    """Return the monthly recurring total for BOM rows."""
    return sum(item["price_mrc"] * item["qty"] for item in bom)


def _replace_items(bom, replacements, catalog):
    updated = []
    for item in bom:
        replacement = replacements.get(item["item"])
        if replacement is None:
            updated.append(dict(item))
            continue
        updated.append({**item, "item": replacement, **catalog[replacement]})
    return updated


def get_budget_tradeoffs(bom, product_keys, catalog, product_materials):
    """Return concrete, one-step BOM changes ordered by savings."""
    options = []
    present = {item["item"] for item in bom}

    for port, lower_port in PORT_DOWNGRADES.items():
        if port not in present:
            continue
        replacements = {port: lower_port}
        optic = PORT_OPTICS[port]
        lower_optic = PORT_OPTICS[lower_port]
        if optic in present:
            replacements[optic] = lower_optic
        updated = _replace_items(bom, replacements, catalog)
        options.append({
            "id": f"speed:{port}",
            "label": f"Lower connection speed to {lower_port.replace('_Port', '')}",
            "question": "Can we lower the connection speed to reduce the monthly cost?",
            "bom": updated,
        })

    paired_optics = {PORT_OPTICS[port] for port in PORT_OPTICS if port in present}
    for optic, lower_optic in OPTIC_DOWNGRADES.items():
        if optic in present and optic not in paired_optics:
            options.append({
                "id": f"optic:{optic}",
                "label": f"Downgrade hardware from {optic.replace('Optic_', '')} to {lower_optic.replace('Optic_', '')}",
                "question": "Would a lower-speed optic meet your needs?",
                "bom": _replace_items(bom, {optic: lower_optic}, catalog),
            })

    if "DDoS_Advanced" in present and "DDoS_Basic" not in present:
        options.append({
            "id": "security:ddos-basic",
            "label": "Reduce DDoS protection from Advanced to Basic",
            "question": "Is Basic DDoS protection sufficient instead of Advanced protection?",
            "bom": _replace_items(bom, {"DDoS_Advanced": "DDoS_Basic"}, catalog),
        })

    required = {
        item
        for product in product_keys
        for item in product_materials.get(product, {}).get("required", [])
    }
    optional = {
        item
        for product in product_keys
        for item in product_materials.get(product, {}).get("optional", [])
    }
    removable = (optional | {
        item["item"] for item in bom if item["category"] == "Security"
    }) - required
    for item_key in sorted(removable & present):
        item = next(row for row in bom if row["item"] == item_key)
        updated = [dict(row) for row in bom if row["item"] != item_key]
        options.append({
            "id": f"remove:{item_key}",
            "label": f"Remove optional {item['desc']}",
            "question": f"Can we remove {item['desc']} from this quote?",
            "bom": updated,
        })

    for option in options:
        option["mrc"] = calculate_mrc(option["bom"])
        option["savings"] = calculate_mrc(bom) - option["mrc"]
    return sorted(options, key=lambda option: option["savings"], reverse=True)