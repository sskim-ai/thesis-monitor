"""Pure migration planning, not scheduler installation or activation."""

from pathlib import Path


RETIRED_AUTOMATIONS = (
    "thesis-monitor-ai-review-us-primary", "thesis-monitor-ai-review-us-backup",
    "thesis-monitor-ai-review-kr-primary", "thesis-monitor-ai-review-kr-backup",
)
RETIRED_AGENTS = (
    "com.seungsoo.thesis-monitor.daily", "com.seungsoo.thesis-monitor.kr-close",
    "com.seungsoo.thesis-monitor.ai-review-fallback",
    "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
)


def migration_plan(operating: Path, python: Path, *, host_timezone: str) -> dict:
    if host_timezone != "Asia/Seoul":
        raise ValueError("launchd_schedule_requires_verified_kst_host")
    agents = []
    for market, hour, minute in (("us", 8, 10), ("kr", 16, 0)):
        label = "com.seungsoo.thesis-monitor.unified-" + market
        agents.append({
            "Label": label, "Disabled": True,
            "ProgramArguments": [str(python), "-m", "app.jobs.unified_market_snapshot", "--market", market],
            "WorkingDirectory": str(operating),
            "StartCalendarInterval": {"Hour": hour, "Minute": minute},
            "StandardOutPath": str(operating / "logs" / (label + ".out.log")),
            "StandardErrorPath": str(operating / "logs" / (label + ".err.log")),
        })
    return {"contract": "unified-scheduler-migration-plan-v1", "status": "NOT_APPLIED",
            "activation_allowed": False, "disable_app_automations": list(RETIRED_AUTOMATIONS),
            "bootout_and_disable_launch_agents": list(RETIRED_AGENTS), "new_agents": agents,
            "preserve": ["api_service", "onboarding_reconciler", "krx_telemetry", "night_publication_observer"],
            "required_gates": ["concrete_production_adapter_qualified", "full_regression_pass",
                               "promotion_authorized", "old_jobs_durably_disabled",
                               "icloud_destination_verified", "single_entry_after_inventory"],
            "rollback": "disable both new jobs before restoring any prior topology; no concurrent paths"}
