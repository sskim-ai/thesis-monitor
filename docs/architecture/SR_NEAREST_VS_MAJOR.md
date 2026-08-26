# SR Nearest Versus Major

`nearest` first applies the common confirmation and width quality floor, then minimizes
distance from current price on the requested side. `major` first excludes inactive remote zones,
then ranks structural timeframe, independent source evidence, confirmation, recency, bounded
reaction count, and distance. The two fields may coincide when only one eligible zone exists, but
they are not the same ranking by construction. A current zone is a separate object.
