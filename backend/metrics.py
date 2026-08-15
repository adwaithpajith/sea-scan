def compute_voyage_metrics(distance_nm):
    days         = distance_nm / (24*24)
    fuel_tonnes  = 180 * days
    return {
        "distance_nm"     : distance_nm,
        "duration_days"   : round(days, 1),
        "fuel_tonnes"     : round(fuel_tonnes),
        "co2_tonnes"      : round(fuel_tonnes * 3.114),
        "fuel_cost_usd"   : round(fuel_tonnes * 650),
        "cost_per_teu_usd": round((fuel_tonnes * 650) / 10000),
    }

def compute_risk_score(weather_score, conflict_score):
    score = round((conflict_score*0.6) + (weather_score*0.4), 1)
    return {
        "risk_score": score,
        "risk_label": ("Low Risk"      if score<3 else
                       "Moderate Risk" if score<5 else
                       "Elevated Risk" if score<7 else "High Risk"),
        "risk_color": ("#2ecc71" if score<3 else
                       "#f39c12" if score<5 else
                       "#e67e22" if score<7 else "#e74c3c"),
    }

def compute_efficiency_scores(routes):
    if not routes: return []
    dists = [r["metrics"]["distance_nm"]     for r in routes]
    co2s  = [r["metrics"]["co2_tonnes"]      for r in routes]
    costs = [r["metrics"]["cost_per_teu_usd"] for r in routes]
    def norm(v, vals):
        mn,mx = min(vals),max(vals)
        return 0.0 if mx==mn else round((v-mn)/(mx-mn)*10, 1)
    for r in routes:
        e = round(norm(r["metrics"]["distance_nm"],dists)*0.5 +
                  norm(r["metrics"]["co2_tonnes"],co2s)*0.25 +
                  norm(r["metrics"]["cost_per_teu_usd"],costs)*0.25, 1)
        r["efficiency_score"] = e
        r["efficiency_label"] = ("Highly Efficient" if e<2.5 else
                                 "Efficient"        if e<5.0 else
                                 "Moderate"         if e<7.5 else "Inefficient")
    return routes

def tag_extremes(routes):
    """
    Tag the lowest-risk route(s) and the most-efficient route(s) independently.
    This is intentionally NOT a single "recommended" route: Sea Scan's MCDM
    philosophy keeps Risk and Efficiency as separate, co-equal objectives, so
    both extremes are surfaced side by side and the user still makes the call.
    Ties are all tagged true rather than arbitrarily picking one.
    """
    if not routes:
        return routes
    min_risk = min(r["risk_score"] for r in routes)
    min_eff  = min(r["efficiency_score"] for r in routes)
    for r in routes:
        r["lowest_risk"]    = (r["risk_score"] == min_risk)
        r["most_efficient"] = (r["efficiency_score"] == min_eff)
    return routes

def score_all_routes(routes, weather_results, conflict_results):
    enriched = []
    for i, route in enumerate(routes):
        m   = compute_voyage_metrics(route["distance"])
        rs  = compute_risk_score(
                  weather_results[i]["weather_risk_score"],
                  conflict_results[i]["conflict_risk_score"])
        enriched.append({
            **route,
            "metrics"          : m,
            "weather"          : weather_results[i],
            "conflict"         : conflict_results[i],
            "risk_score"       : rs["risk_score"],
            "risk_label"       : rs["risk_label"],
            "risk_color"       : rs["risk_color"],
            "efficiency_score" : 0,
            "efficiency_label" : "",
        })
    enriched = compute_efficiency_scores(enriched)
    return tag_extremes(enriched)
