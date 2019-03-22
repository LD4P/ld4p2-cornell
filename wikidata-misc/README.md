# Wikidata Experiment

## `wikidata-watch.py
`
Might it be possible to use the MediaWiki `feedrecentchanges` API as a source of entities updates (Q numbers) that can then be used to dereference the entities and maintain an up-to-date copy of wikidata RDF?

Preliminary results suggest:

  * There are ~2 updates/s seen via this API (around 2019-03-22)
  * There is some update frequency of the `feedrecentchanges` API that is not frequent enough to keep up with the limit of 50 updates per request

but also:

  * The `https://www.wikidata.org/entity/Q###` requests don't actually return the data we might want
  * The WDQS SPARLQ endpoint seems to be quite some time out-of-date with respect to the source data. Having added 'harp player' as an occupation to <https://www.wikidata.org/wiki/Q3539639> it does not show in the output of this [SPARQL query](https://query.wikidata.org/#SELECT%20%3Fp%20%3Fo%20%3FoLabel%20WHERE%20%7B%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22%5BAUTO_LANGUAGE%5D%2Cen%22.%20%7D%0A%20%20wd%3AQ3539639%20%3Fp%20%3Fo.%0A%7D%0ALIMIT%20100) and the page says it is using data from 3h ago.
  * So, seems like a dead end, not sure how to get up-to-data data??