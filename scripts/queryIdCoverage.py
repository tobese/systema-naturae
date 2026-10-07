import duckdb
con = duckdb.connect()

q = 'SELECT count(*) FROM read_parquet("portal/data/species.parquet")'
con.execute(q)
total = con.fetchone()[0]

con.execute('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE id IS NOT NULL AND length(id) > 0')
with_id = con.fetchone()[0]

con.execute('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE hasDescription')
with_desc = con.fetchone()[0]

con.execute('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE authorityIds IS NOT NULL AND length(authorityIds) > 0')
with_source = con.fetchone()[0]

con.execute("SELECT count(*) FROM read_parquet('portal/data/species.parquet') WHERE sourcedFrom = 'wikipedia'")
wiki_sourced = con.fetchone()[0]

con.execute('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE iucnStatus IS NOT NULL AND length(iucnStatus) > 0')
with_iucn = con.fetchone()[0]

con.execute('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE hasDescription AND authorityIds IS NOT NULL AND length(authorityIds) > 0')
desc_and_source = con.fetchone()[0]

con.execute('''
    WITH split_ids AS (
        SELECT unnest(string_split(authorityIds, ',')) as auth
        FROM read_parquet("portal/data/species.parquet")
        WHERE authorityIds IS NOT NULL AND length(authorityIds) > 0
    )
    SELECT auth, count(*) as n FROM split_ids GROUP BY auth ORDER BY n DESC
''')
auths = con.fetchall()

con.execute('''SELECT kingdom, count(*) as total, 
    sum(CASE WHEN id IS NOT NULL AND length(id) > 0 THEN 1 ELSE 0 END) as with_id,
    sum(CASE WHEN hasDescription THEN 1 ELSE 0 END) as with_desc,
    sum(CASE WHEN authorityIds IS NOT NULL AND length(authorityIds) > 0 THEN 1 ELSE 0 END) as with_source,
    sum(CASE WHEN sourcedFrom = 'wikipedia' THEN 1 ELSE 0 END) as wiki_sourced,
    sum(CASE WHEN iucnStatus IS NOT NULL AND length(iucnStatus) > 0 THEN 1 ELSE 0 END) as with_iucn
    FROM read_parquet("portal/data/species.parquet")
    GROUP BY kingdom ORDER BY total DESC''')
kingdoms = con.fetchall()

print(f'Total species: {total:,}')
print(f'With id: {with_id:,} ({with_id/total*100:.1f}%)')
print(f'With description: {with_desc:,} ({with_desc/total*100:.1f}%)')
print(f'With sourceIds: {with_source:,} ({with_source/total*100:.1f}%)')
print(f"Sourced from wikipedia: {wiki_sourced:,} ({wiki_sourced/total*100:.1f}%)")
print(f'With IUCN status: {with_iucn:,} ({with_iucn/total*100:.1f}%)')
print(f'With description AND sourceIds: {desc_and_source:,} ({desc_and_source/total*100:.1f}%)')
print()
print('Authority IDs breakdown:')
for auth, n in auths:
    print(f'  {auth:15s} {n:>10,} ({n/total*100:.2f}%)')
print()
print('By kingdom:')
print(f'{"Kingdom":<12} {"Total":>10} {"with_id":>10} {"desc%":>8} {"src%":>8} {"wiki%":>8} {"iucn%":>8}')
for row in kingdoms:
    k, tot, wid, wdesc, wsrc, wiki, wiucn = row
    print(f'{k:<12} {tot:>10,} {wid:>10,} {wdesc/tot*100:>7.1f}% {wsrc/tot*100:>7.1f}% {wiki/tot*100:>7.1f}% {wiucn/tot*100:>7.1f}%')
