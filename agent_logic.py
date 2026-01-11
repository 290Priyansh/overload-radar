import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
DATA_FILE = "burnout_data.csv"

CRITICAL_THRESHOLD = 75
AT_RISK_THRESHOLD = 55
# ---------------------------------------


def run_burnout_agent():
    print(" Burnout Agent running...")

    # ---------- LOAD DATA ----------
    df = pd.read_csv(DATA_FILE)

    # ---------- DERIVE BURNOUT SCORE ----------
    # Transparent + explainable formula
    df["Burnout_Score"] = (
        (df["Total_Weekly_Hours"] * 1.0)
        + (df["Overtime_Hours"] * 3.0)
        - (df["Avg_Days_Early"] * 2.0)
    )

    # Clamp score between 0–100
    df["Burnout_Score"] = df["Burnout_Score"].clip(0, 100)

    # ---------- COMPANY BASELINE ----------
    company_avg = df["Burnout_Score"].mean()

    # ---------- DEPARTMENT ANALYSIS ----------
    dept_avg = (
        df.groupby("Department")["Burnout_Score"]
        .mean()
        .sort_values(ascending=False)
    )

    risky_departments = dept_avg[dept_avg >= AT_RISK_THRESHOLD]

    if risky_departments.empty:
        send_healthy_report(company_avg)
        return

    # ---------- SUB-TEAM ROOT CAUSE ----------
    subteam_analysis = (
        df.groupby(["Department", "Sub_Team"])
        .agg(
            avg_burnout=("Burnout_Score", "mean"),
            avg_hours=("Total_Weekly_Hours", "mean"),
            avg_overtime=("Overtime_Hours", "mean"),
        )
        .reset_index()
    )

    # ---------- INDIVIDUAL SIGNAL (PRIVACY SAFE) ----------
    overloaded_people = df[df["Burnout_Score"] >= 85]
    impacted_count = overloaded_people["Employee_ID"].nunique()

    # ---------- BUILD SLACK REPORT ----------
    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "📊 Weekly Burnout Intelligence Report",
            "emoji": True
        }
    })

    # Company baseline
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Company Average Burnout:* `{company_avg:.1f}%`"
        }
    })

    # Department risk summary
    dept_lines = []
    for dept, score in risky_departments.items():
        delta = ((score - company_avg) / company_avg) * 100
        level = "🔴 Critical" if score >= CRITICAL_THRESHOLD else "🟡 At Risk"
        dept_lines.append(
            f"*{dept}* — `{score:.1f}%` ({delta:+.1f}% vs avg) {level}"
        )

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*High-Risk Departments:*\n" + "\n".join(dept_lines)
        }
    })

    # Root cause drivers
    root_lines = []
    for dept in risky_departments.index:
        top_teams = (
            subteam_analysis[subteam_analysis["Department"] == dept]
            .sort_values("avg_burnout", ascending=False)
            .head(2)
        )
        for _, row in top_teams.iterrows():
            root_lines.append(
                f"*{dept} → {row['Sub_Team']}*\n"
                f"• Avg weekly hours: `{row['avg_hours']:.1f}`\n"
                f"• Overtime: `{row['avg_overtime']:.1f}h`"
            )

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Primary Drivers:*\n" + "\n".join(root_lines)
        }
    })

    # Individual impact (privacy aware)
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "*Individual Impact:*\n"
                f"• `{impacted_count}` contributors showing sustained overload\n"
                "• Pattern indicates *systemic*, not individual, risk"
            )
        }
    })

    # Recommendations
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "*Recommended Actions:*\n"
                "• Declare a meeting-free day this week\n"
                "• Rebalance sprint commitments\n"
                "• Review overtime & on-call rotations"
            )
        }
    })

    # CTA
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "📈 View Tableau Evidence",
                    "emoji": True
                },
                "url": "https://public.tableau.com/app/profile/priyansh.v4388/viz/Burnout_Dasboard/OrganizationDrill-Down?publish=yes"
            }
        ]
    })

    send_to_slack(blocks)


def send_healthy_report(company_avg):
    payload = {
        "text": f"🟢 Weekly Burnout Report: All teams healthy (Avg {company_avg:.1f}%)."
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)


def send_to_slack(blocks):
    payload = {"blocks": blocks}
    response = requests.post(
        SLACK_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    if response.status_code == 200:
        print("✅ Slack report sent")
    else:
        print("Slack error:", response.text)


if __name__ == "__main__":
    run_burnout_agent()
