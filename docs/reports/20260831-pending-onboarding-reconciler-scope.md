# Pending Onboarding Reconciler Scope

Base `9c0e2907a5914f43e257cd886d25078288f1bba4` and exact instruction commit `c95e176` lead to implementation `5e3820456ace797450b9403386edaa2fc6af6cf1`. The implementation extends the existing readiness coordinator; it does not create a parallel activation path.

Three bounded entry points share one subject-level coordinator: immediate registration continuation, a 30-minute background reconciler, and market-scoped packet preflight. They operate only on explicitly requested pending subjects. Ready peers and the opposite market never wait for one subject.

The reconciler owns attempts and retry metadata. The existing readiness validator remains the only authority that can activate a subject. Production messages, accepted history, Price Structure, valuation, Telegram recipients, and delivery schedules are unchanged.
