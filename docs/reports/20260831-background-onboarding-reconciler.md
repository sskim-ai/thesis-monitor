# Background Onboarding Reconciler

Contract: `pending-onboarding-reconciler-v1`.

LaunchAgent `com.seungsoo.thesis-monitor.onboarding-reconciler` runs every 1800 seconds with `RunAtLoad=false`. Each run discovers requested pending subjects, applies due-time and retry-class gates, limits the cohort, isolates failures per subject, and reports aggregate observability. It never sends Telegram or starts a delivery task.

Post-control state: pending `0`, retryable `0`, review-required `0`, active-ready `22`. A second generic deployment-smoke run attempted `0`, proving idempotent convergence.
