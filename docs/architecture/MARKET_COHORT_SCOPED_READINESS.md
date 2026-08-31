# Market Cohort Scoped Readiness

Readiness is evaluated for the target market, session, packet cutoff, and subject.

KR selection never inspects a US pending subject, and US selection never inspects a KR pending subject. Within one market, a subject that is pending or loses required profile evidence is excluded with a subject-level reason; ready peers continue.

Packet-wide abort is reserved for shared integrity failures such as a corrupt market packet or an unreadable shared gate. Ordinary company-profile incompleteness is not a packet-wide failure.

Numeric-semantic validation consumes only registries from the frozen packet cohort. V2 candidate creation consumes `packet.stocks`, which is the same cohort, rather than querying the global watchlist.
