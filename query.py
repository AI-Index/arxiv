import arxiv
import maya
import time

"""
Notes

    - This uses the classic Arxiv API which does not appear to support date range queries
        - Why is that? Reach out to make sure that's true.
    - According to blog posts they are revamping both search and the API right now
        - https://blogs.cornell.edu/arxiv/2018/03/02/engaging-external-developers-in-arxiv-ng/
        - https://blogs.cornell.edu/arxiv/2018/04/17/new-release-arxiv-search-v0-1/
            - https://arxiv.org/search/advanced
    - The new elasticsearch based search *does* support date range queries
    - Third parties have date range based queries in their tools.
        - 
"""


def main():

    # Build Query String
    query_string = ''

    # Categories
    # See https://arxiv.org/help/api/user-manual#subject_classifications for all
    # categories available.
    cats = ['cs.AI']
    if len(cats) > 0:
        cat_part = 'cat:' + ' OR '.join(cats)
        query_string += cat_part

    # Search terms
    terms = []
    if len(terms) > 0:
        term_part = ' all:' + ' AND '.join(terms)
        query_string += term_part

    # Get the list of results and meta information about the result set.
    entries, meta = arxiv.query(
        search_query=query_string,
        sort_by='submittedDate',
        max_results=1,
        start=5408,
    )
    total_count = int(meta.opensearch_totalresults)
    print("There are {} total papers that match this query. Finding oldest ...".format(total_count))

    # What is the oldest paper we want to count?
    cutoff = maya.when('January 1st, 2018')

    # Narrow things down with
    start = total_count // 2
    next_step = start // 2
    while True:
        if next_step == 0:
            print(start)
            break

        # Get the item
        time.sleep(3)
        print("Getting item {}".format(start))
        while True:
            entries, meta = arxiv.query(
                search_query=query_string,
                sort_by='submittedDate',
                max_results=1,
                start=start
            )
            try:
                entry = entries[0]
                break
            except IndexError:
                print("Fail. Retrying")
                time.sleep(3)

        published_date = maya.parse(entry.published)
        # Too old
        if published_date < cutoff:
            print("Too old ...")
            start -= next_step
        # Too new
        elif published_date > cutoff:
            print("Too new ...")
            # Bail out and get all the rest
            if next_step < 100:
                break

            start += next_step

        next_step = next_step // 2

    time.sleep(3)
    remaining = (next_step * 2) + 1
    print("Getting remaining {} items starting with {}".format(remaining, start))
    entries, meta = arxiv.query(
        search_query=query_string,
        sort_by='submittedDate',
        max_results=remaining,
        start=start
    )

    oldest_after_cutoff = -1
    for i, entry in enumerate(entries):
        published_date = maya.parse(entry.published)
        if published_date < cutoff:
            oldest_after_cutoff = i - 1
            print("Found oldest after cutoff ...")
            break

    result_num = start + oldest_after_cutoff
    print("There have been {} articles that match this query since {}".format(result_num, cutoff))

if __name__ == '__main__':
    main()
